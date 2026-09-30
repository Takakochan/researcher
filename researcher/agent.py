import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Callable

from .config import Config
from .llm import LLM
from . import prompts
from .search import SearchResult, WebSearch, format_results


@dataclass
class ResearchState:
    topic: str
    query: str = ""
    summary: str = ""
    loop_count: int = 0
    queries: list[str] = field(default_factory=list)
    knowledge_gaps: list[str] = field(default_factory=list)
    sources: list[SearchResult] = field(default_factory=list)


class ResearchAgent:
    def __init__(self, config: Config, on_event: Callable[[str, dict], None] | None = None):
        self.config = config
        self.llm = LLM(config)
        self.search = WebSearch(config)
        self.on_event = on_event or (lambda event, data: None)

    def run(self, topic: str) -> ResearchState:
        state = ResearchState(topic=topic)

        # 1. 調査タスクから最初の検索クエリを生成
        state.query = self.generate_query(topic)

        while True:
            state.loop_count += 1
            self.on_event("loop_start", {"loop": state.loop_count, "query": state.query})
            state.queries.append(state.query)

            # 2. Tavily で情報源を探索
            results = self.web_search(state.query)
            state.sources.extend(results)

            # 3. 検索結果を LLM で要約（既存の要約を逐次更新）
            state.summary = self.summarize(state, results)

            if state.loop_count >= self.config.max_research_loops:
                break

            # 4. 要約を振り返り、不足している知識を特定
            # 5. 不足を解消するための新たな検索クエリを生成
            gap, next_query = self.reflect(state)
            state.knowledge_gaps.append(gap)
            state.query = next_query

        self.on_event("done", {"state": state})
        return state

    def generate_query(self, topic: str) -> str:
        data = self.llm.chat_json(
            prompts.QUERY_WRITER.format(today=date.today().isoformat()),
            f"調査タスク: {topic}",
        )
        query = data.get("query") or topic
        self.on_event("query", {"query": query, "rationale": data.get("rationale", "")})
        return query

    def web_search(self, query: str) -> list[SearchResult]:
        results = self.search.search(query)
        self.on_event("search", {"results": results})
        return results

    def summarize(self, state: ResearchState, results: list[SearchResult]) -> str:
        if state.summary:
            user = (
                f"調査タスク: {state.topic}\n\n"
                f"<既存の要約>\n{state.summary}\n</既存の要約>\n\n"
                f"<新しい検索結果>\n{format_results(results)}\n</新しい検索結果>"
            )
        else:
            user = (
                f"調査タスク: {state.topic}\n\n"
                f"<検索結果>\n{format_results(results)}\n</検索結果>"
            )
        summary = self.llm.chat(prompts.SUMMARIZER, user)
        self.on_event("summary", {"summary": summary})
        return summary

    def reflect(self, state: ResearchState) -> tuple[str, str]:
        data = self.llm.chat_json(
            prompts.REFLECTION.format(today=date.today().isoformat()),
            f"調査タスク: {state.topic}\n\n<現在の要約>\n{state.summary}\n</現在の要約>",
        )
        gap = data.get("knowledge_gap", "")
        query = data.get("follow_up_query") or f"{state.topic} 詳細"
        self.on_event("reflection", {"knowledge_gap": gap, "query": query})
        return gap, query


def build_report(state: ResearchState) -> str:
    seen: set[str] = set()
    source_lines = []
    for s in state.sources:
        if s.url and s.url not in seen:
            seen.add(s.url)
            source_lines.append(f"- [{s.title or s.url}]({s.url})")

    query_lines = [f"{i}. {q}" for i, q in enumerate(state.queries, 1)]
    return (
        f"# 調査レポート: {state.topic}\n\n"
        f"## 要約\n\n{state.summary}\n\n"
        f"## 使用した検索クエリ\n\n" + "\n".join(query_lines) + "\n\n"
        f"## 情報源\n\n" + "\n".join(source_lines) + "\n"
    )


def save_report(report: str, topic: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w\-]+", "_", topic)[:40].strip("_")
    path = out_dir / f"{datetime.now():%Y%m%d_%H%M%S}_{slug}.md"
    path.write_text(report, encoding="utf-8")
    return path
