# main.py
import logging
from tqdm import tqdm
import time
from config import config
from text_processor import TextProcessor
from model_integration import ModelIntegration
from knowledge_graph import KnowledgeGraphBuilder
from neo4j_store import Neo4jStore


def setup_logging():
    """配置日志系统"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 文件日志
    file_handler = logging.FileHandler(config.LOG_FILE)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def main():
    # 初始化
    logger = setup_logging()
    config.log_config(logger)

    # 初始化组件
    text_processor = TextProcessor(config.TEXT_CHUNK_SIZE)
    model_integration = ModelIntegration()
    kg_builder = KnowledgeGraphBuilder()
    neo4j_store = Neo4jStore()

    try:
        # 读取并处理文本
        novel_text = text_processor.read_novel(config.NOVEL_FILE)
        chunks = text_processor.split_text(novel_text)

        # 处理每个文本块
        for i, chunk in enumerate(tqdm(chunks, desc="处理小说文本")):
            logger.info(f"处理区块 {i + 1}/{len(chunks)}")

            # 知识提取
            raw_knowledge = model_integration.extract_knowledge(chunk)

            # 知识规范化
            normalized_knowledge = kg_builder.normalize_knowledge(raw_knowledge, i)

            # 存储到Neo4j
            neo4j_store.store_knowledge(normalized_knowledge, kg_builder)

            # 避免频繁调用API
            time.sleep(0.5)

        logger.info("知识图谱构建完成！")
    except Exception as e:
        logger.exception("处理过程中发生严重错误")
    finally:
        neo4j_store.close()


if __name__ == "__main__":
    main()