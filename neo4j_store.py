# neo4j_store.py
from neo4j import GraphDatabase, basic_auth
import logging
from config import config


class Neo4jStore:
    def __init__(self):
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self._connect()
        self._create_constraints()

    def _connect(self):
        """连接Neo4j数据库"""
        try:
            # 修正：添加缺失的右括号
            self.driver = GraphDatabase.driver(
                config.NEO4J_URI,
                auth=basic_auth(config.NEO4J_USER, config.NEO4J_PASSWORD)
            )
            self.logger.info("成功连接Neo4j数据库")
        except Exception as e:
            self.logger.error(f"连接Neo4j失败: {str(e)}")
            raise

    def _create_constraints(self):
        """创建唯一约束确保数据一致性"""
        with self.driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Item) REQUIRE i.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Time) REQUIRE t.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Event) REQUIRE e.name IS UNIQUE"
            ]
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    self.logger.warning(f"创建约束失败: {constraint}, 错误: {str(e)}")

    def store_knowledge(self, knowledge, kg_builder):
        """将提取的知识存储到Neo4j"""
        if not knowledge:
            self.logger.warning("尝试存储空知识对象")
            return

        with self.driver.session() as session:
            # 存储实体
            for entity in knowledge.get("entities", []):
                # 确保实体有必要的字段
                if "name" not in entity or "type" not in entity:
                    self.logger.warning(f"跳过无效实体: {entity}")
                    continue

                try:
                    session.execute_write(
                        self._merge_node,
                        entity["type"].capitalize(),
                        {"name": entity["name"]}
                    )
                except Exception as e:
                    self.logger.error(f"存储实体失败: {entity}, 错误: {str(e)}")

            # 存储事件
            for event in knowledge.get("events", []):
                # 确保事件有名称
                if "name" not in event:
                    self.logger.warning(f"跳过无名称事件: {event}")
                    continue

                try:
                    # 创建事件节点
                    session.execute_write(
                        self._merge_node,
                        "Event",
                        {
                            "name": event["name"],
                            "cause": event.get("cause", ""),
                            "process": event.get("process", ""),
                            "result": event.get("result", ""),
                            "chunk_index": event.get("chunk_index", -1)
                        }
                    )

                    # 连接事件参与者
                    for participant in event.get("participants", []):
                        if not participant:
                            continue

                        # 为参与者创建节点（如果不存在）
                        session.execute_write(
                            self._merge_node,
                            "Person",
                            {"name": participant}
                        )

                        # 创建参与关系
                        session.execute_write(
                            self._merge_relationship,
                            "Person", participant,
                            "Event", event["name"],
                            "PARTICIPATED_IN", {}
                        )

                    # 连接事件时间
                    if event.get("time"):
                        session.execute_write(
                            self._merge_node,
                            "Time",
                            {"name": event["time"]}
                        )
                        session.execute_write(
                            self._merge_relationship,
                            "Event", event["name"],
                            "Time", event["time"],
                            "OCCURRED_AT", {}
                        )

                    # 连接事件地点
                    if event.get("location"):
                        session.execute_write(
                            self._merge_node,
                            "Location",
                            {"name": event["location"]}
                        )
                        session.execute_write(
                            self._merge_relationship,
                            "Event", event["name"],
                            "Location", event["location"],
                            "OCCURRED_AT", {}
                        )
                except Exception as e:
                    self.logger.error(f"存储事件失败: {event['name']}, 错误: {str(e)}")

            # 存储关系
            for rel in knowledge.get("relationships", []):
                # 验证关系数据
                if not all(key in rel for key in ["source", "target", "type"]):
                    self.logger.warning(f"跳过无效关系: {rel}")
                    continue

                try:
                    # 确定源节点类型
                    source_types = kg_builder.get_entity_types(rel["source"])
                    target_types = kg_builder.get_entity_types(rel["target"])

                    # 为两端创建节点（如果不存在）
                    for entity_name, types in [(rel["source"], source_types), (rel["target"], target_types)]:
                        if not types:
                            types = ["Entity"]

                        for entity_type in types:
                            session.execute_write(
                                self._merge_node,
                                entity_type,
                                {"name": entity_name}
                            )

                    # 创建关系
                    session.execute_write(
                        self._merge_relationship,
                        None, rel["source"],
                        None, rel["target"],
                        rel["type"], {}
                    )
                except Exception as e:
                    self.logger.error(f"存储关系失败: {rel['source']}-{rel['type']}->{rel['target']}, 错误: {str(e)}")

    def _merge_node(self, tx, label, properties):
        """创建或更新节点"""
        if not properties or "name" not in properties:
            self.logger.error(f"无效节点属性: {properties}")
            return

        try:
            query = f"""
            MERGE (n:{label} {{name: $name}})
            SET n += $properties
            RETURN id(n)
            """
            params = {"name": properties["name"], "properties": properties}
            result = tx.run(query, **params)
            return result.single()[0] if result else None
        except Exception as e:
            self.logger.error(f"创建节点失败: {label} {properties}, 错误: {str(e)}")
            raise

    def _merge_relationship(self, tx, source_label, source_name,
                            target_label, target_name, rel_type, rel_props):
        """创建或更新关系"""
        if not source_name or not target_name or not rel_type:
            self.logger.error(f"无效关系参数: {source_name}->{target_name} ({rel_type})")
            return

        try:
            # 自动推断标签
            source_clause = f":{source_label}" if source_label else ""
            target_clause = f":{target_label}" if target_label else ""

            query = f"""
            MERGE (s{source_clause} {{name: $source_name}})
            MERGE (t{target_clause} {{name: $target_name}})
            MERGE (s)-[r:{rel_type}]->(t)
            SET r += $rel_props
            """
            params = {
                "source_name": source_name,
                "target_name": target_name,
                "rel_props": rel_props
            }
            tx.run(query, **params)
        except Exception as e:
            self.logger.error(f"创建关系失败: {source_name}-{rel_type}->{target_name}, 错误: {str(e)}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.driver:
            try:
                self.driver.close()
                self.logger.info("Neo4j连接已关闭")
            except Exception as e:
                self.logger.error(f"关闭Neo4j连接失败: {str(e)}")