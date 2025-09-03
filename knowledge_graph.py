# knowledge_graph.py
import logging
from collections import defaultdict
from config import config


class KnowledgeGraphBuilder:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.entity_cache = defaultdict(set)  # 缓存已处理实体

    def normalize_knowledge(self, raw_knowledge, chunk_index):
        """规范化知识结构并过滤重复实体"""
        normalized = {
            "entities": [],
            "events": [],
            "relationships": []
        }

        # 处理实体
        seen_entities = set()
        for entity in raw_knowledge.get("entities", []):
            entity_key = (entity["name"], entity["type"])
            if entity_key not in seen_entities:
                seen_entities.add(entity_key)
                normalized["entities"].append(entity)
                # 添加到全局缓存
                self.entity_cache[entity["name"]].add(entity["type"])

        # 处理事件
        for event in raw_knowledge.get("events", []):
            # 确保事件有名称
            if not event.get("name"):
                continue

            # 规范化参与者
            participants = []
            for p in event.get("participants", []):
                if p and isinstance(p, str):
                    participants.append(p)

            normalized_event = {
                "name": event["name"],
                "participants": participants,
                "time": event.get("time", ""),
                "location": event.get("location", ""),
                "cause": event.get("cause", ""),
                "process": event.get("process", ""),
                "result": event.get("result", ""),
                "chunk_index": chunk_index  # 记录来源区块
            }
            normalized["events"].append(normalized_event)

        # 处理关系
        for rel in raw_knowledge.get("relationships", []):
            if all(key in rel for key in ["source", "target", "type"]):
                normalized["relationships"].append({
                    "source": rel["source"],
                    "target": rel["target"],
                    "type": rel["type"]
                })

        self.logger.info(f"区块 {chunk_index}: 提取实体 {len(normalized['entities'])}个, "
                         f"事件 {len(normalized['events'])}个, 关系 {len(normalized['relationships'])}个")
        return normalized

    def get_entity_types(self, entity_name):
        """获取实体的可能类型"""
        return list(self.entity_cache.get(entity_name, ["Entity"]))