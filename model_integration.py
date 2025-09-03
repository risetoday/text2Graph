# model_integration.py
import json
import requests
import time
import logging
from config import config


class ModelIntegration:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {"Content-Type": "application/json"}

    def extract_knowledge(self, text_chunk):
        """使用大模型从文本中提取结构化知识"""
        prompt = self._build_prompt(text_chunk)
        return self._call_model_api(prompt)

    def _build_prompt(self, text_chunk):
        """构建知识提取提示词"""
        return f"""
        你是一个知识提取专家，请从以下小说文本中提取结构化信息：

        需要提取的要素：
        1. 实体类型: 
           - 人物(Person): 小说中出现的人名
           - 物品(Item): 有意义的物品
           - 组织(Organization): 团体或机构
           - 时间(Time): 具体时间点或时期
           - 地点(Location): 地理位置
        2. 事件(Event): 
           - 事件名称
           - 参与者(人物)
           - 发生时间
           - 发生地点
           - 起因
           - 经过
           - 结果
        3. 关系:
           - 人物关系: 家庭关系/社会关系等
           - 事件关系: 因果/时序关系

        输出要求：
        - 使用严格JSON格式
        - 结构如下：
          {{
            "entities": [
              {{"name": "实体名称", "type": "实体类型(Person/Item/Organization/Time/Location)"}}
            ],
            "events": [
              {{
                "name": "事件名称",
                "participants": ["人物1", "人物2"],
                "time": "时间",
                "location": "地点",
                "cause": "起因",
                "process": "经过",
                "result": "结果"
              }}
            ],
            "relationships": [
              {{"source": "来源实体", "target": "目标实体", "type": "关系类型"}}
            ]
          }}

        注意：
        - 实体名称必须统一（同一个人物用同一个名字）
        - 事件名称要简洁明确
        - 关系类型用中文描述，如"父亲"、"朋友"、"导致"等

        文本内容：
        {text_chunk}
        """

    def _call_model_api(self, prompt, retry_count=0):
        """调用模型API进行信息抽取"""
        payload = {
            "model": config.MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": config.MODEL_TEMPERATURE,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(
                config.MODEL_API,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return json.loads(result["choices"][0]["message"]["content"])
        except Exception as e:
            if retry_count < config.MAX_RETRIES:
                self.logger.warning(f"API调用失败，重试中... ({retry_count + 1}/{config.MAX_RETRIES})")
                time.sleep(config.RETRY_DELAY)
                return self._call_model_api(prompt, retry_count + 1)
            self.logger.error(f"API调用失败: {str(e)}")
            return {
                "entities": [],
                "events": [],
                "relationships": []
            }