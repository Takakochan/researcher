from dataclasses import dataclass

from tavily import TavilyClient

from .config import Config

MAX_CHARS_PER_SOURCE = 4000


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    raw_content: str | None = None


class WebSearch:
    def __init__(self, config: Config):
        self.client = TavilyClient(api_key=config.tavily_api_key)
        self.max_results = config.tavily_max_results
        self.fetch_full_page = config.fetch_full_page

    def search(self, query: str) -> list[SearchResult]:
        response = self.client.search(
            query=query,
            max_results=self.max_results,
            include_raw_content=self.fetch_full_page,
        )
        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
                raw_content=r.get("raw_content"),
            )
            for r in response.get("results", [])
        ]


def format_results(results: list[SearchResult]) -> str:
    """LLM に渡すための検索結果テキストを作成（URL で重複排除）"""
    seen: set[str] = set()
    blocks = []
    for r in results:
        if r.url in seen:
            continue
        seen.add(r.url)
        block = f"Source: {r.title}\nURL: {r.url}\nSummary: {r.content}"
        if r.raw_content:
            block += f"\nFull content (truncated): {r.raw_content[:MAX_CHARS_PER_SOURCE]}"
        blocks.append(block)
    return "\n\n---\n\n".join(blocks)
