import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _bool(value: str | None) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Config:
    token_factory_api_key: str
    token_factory_base_url: str
    llm_model: str
    tavily_api_key: str
    max_research_loops: int
    tavily_max_results: int
    fetch_full_page: bool

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            token_factory_api_key=os.getenv("TOKEN_FACTORY_API_KEY", ""),
            token_factory_base_url=os.getenv(
                "TOKEN_FACTORY_BASE_URL", "https://api.tokenfactory.nebius.com/v1/"
            ),
            llm_model=os.getenv("LLM_MODEL", "Qwen/Qwen3-235B-A22B-Instruct-2507"),
            tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
            max_research_loops=int(os.getenv("MAX_RESEARCH_LOOPS", "3")),
            tavily_max_results=int(os.getenv("TAVILY_MAX_RESULTS", "3")),
            fetch_full_page=_bool(os.getenv("FETCH_FULL_PAGE", "false")),
        )

    def validate(self) -> None:
        missing = [
            name
            for name, value in (
                ("TOKEN_FACTORY_API_KEY", self.token_factory_api_key),
                ("TAVILY_API_KEY", self.tavily_api_key),
            )
            if not value
        ]
        if missing:
            raise SystemExit(f".env に次の値を設定してください: {', '.join(missing)}")
