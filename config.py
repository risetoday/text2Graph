# config.py
import os


class Config:
    def __init__(self):
        # 模型配置
        self.MODEL_API = os.getenv("MODEL_API", "http://localhost:8000/v1/chat/completions")
        self.MODEL_NAME = os.getenv("MODEL_NAME", "qwen3-14b")
        self.MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", 0.1))

        # Neo4j配置
        self.NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
        self.NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

        # 处理参数
        self.TEXT_CHUNK_SIZE = int(os.getenv("TEXT_CHUNK_SIZE", 1000))
        self.MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
        self.RETRY_DELAY = float(os.getenv("RETRY_DELAY", 5))

        # 文件路径
        self.NOVEL_FILE = os.getenv("NOVEL_FILE", "huozhe.txt")
        self.LOG_FILE = os.getenv("LOG_FILE", "graphrag.log")

    def log_config(self, logger):
        """记录配置信息"""
        config_items = {
            "Model API": self.MODEL_API,
            "Model Name": self.MODEL_NAME,
            "Neo4j URI": self.NEO4J_URI,
            "Text Chunk Size": self.TEXT_CHUNK_SIZE,
            "Novel File": self.NOVEL_FILE
        }
        logger.info("运行配置:")
        for key, value in config_items.items():
            logger.info(f"  {key}: {value}")


# 全局配置实例
config = Config()