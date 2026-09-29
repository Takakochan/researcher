import json
import re

from openai import OpenAI

from .config import Config


class LLM:
    """Token Factory (OpenAI 互換 API) の薄いラッパー"""

    def __init__(self, config: Config):
        self.client = OpenAI(
            api_key=config.token_factory_api_key,
            base_url=config.token_factory_base_url,
        )
        self.model = config.llm_model

    def chat(self, system: str, user: str, temperature: float = 0.3) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return strip_thinking(response.choices[0].message.content or "")

    def chat_json(self, system: str, user: str) -> dict:
        text = self.chat(system, user, temperature=0)
        return parse_json(text)


def strip_thinking(text: str) -> str:
    """推論モデルが出力する <think>...</think> を除去"""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise
