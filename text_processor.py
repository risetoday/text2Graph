# text_processor.py
import re
import logging


class TextProcessor:
    def __init__(self, chunk_size=1000):
        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)

    def split_text(self, text):
        """智能分块文本，保留句子完整性"""
        chunks = []
        start = 0
        text_length = len(text)
        self.logger.info(f"开始文本分块，总长度: {text_length}字符")

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            if end == text_length:
                chunks.append(text[start:end])
                break

            # 在句子边界处分割（中文标点）
            while end > start and text[end] not in {'。', '！', '？', '\n', '；', '…', '”', '》'}:
                end -= 1

            # 如果没找到边界，则按长度分割
            if end == start:
                end = start + self.chunk_size
                # 避免截断一个词（如果可能）
                while end < text_length and not re.match(r'[\s。！？；…’”]', text[end]):
                    end += 1
            else:
                end += 1  # 包含边界字符

            chunks.append(text[start:end])
            start = end

        self.logger.info(f"文本分割为 {len(chunks)} 个区块")
        return chunks

    def read_novel(self, file_path):
        """读取小说文本"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"读取文件失败: {file_path}, 错误: {str(e)}")
            raise