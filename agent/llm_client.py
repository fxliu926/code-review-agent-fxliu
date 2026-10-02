"""LLM 调用模块：封装 OpenAI SDK，支持重试和错误处理。"""
import os
import time

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """封装 LLM 调用。"""

    def __init__(self, model: str = "deepseek-chat", max_retries: int = 3):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if not api_key:
            raise ValueError("未设置 OPENAI_API_KEY，请检查 .env 文件")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_retries = max_retries

    def chat(self, messages: list) -> str:
        """调用 LLM，返回文本。失败时重试。"""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.2,
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                wait = 2 ** attempt
                print(f"[重试 {attempt + 1}/{self.max_retries}] {e}，{wait}s 后重试")
                time.sleep(wait)
        raise RuntimeError(f"LLM 调用失败：{last_error}")
