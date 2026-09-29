import argparse
import re
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .agent import ResearchAgent, build_report
from .config import Config

console = Console()


def print_event(event: str, data: dict) -> None:
    if event == "query":
        console.print(f"[bold cyan]🔎 初期クエリ:[/] {data['query']}")
        if data["rationale"]:
            console.print(f"   [dim]{data['rationale']}[/]")
    elif event == "loop_start":
        console.rule(f"[bold]ループ {data['loop']}")
        console.print(f"[cyan]検索:[/] {data['query']}")
    elif event == "search":
        for r in data["results"]:
            console.print(f"  • {r.title} [dim]{r.url}[/]")
    elif event == "summary":
        console.print("[green]✓ 要約を更新しました[/]")
    elif event == "reflection":
        console.print(f"[yellow]🤔 不足している知識:[/] {data['knowledge_gap']}")
        console.print(f"[yellow]➡ 次のクエリ:[/] {data['query']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Token Factory + Tavily による反復型ウェブリサーチ")
    parser.add_argument("topic", nargs="?", help="調査タスク（省略時は対話入力）")
    parser.add_argument("-n", "--loops", type=int, help="調査ループ回数（.env の MAX_RESEARCH_LOOPS を上書き）")
    parser.add_argument("-o", "--output-dir", default="reports", help="レポート保存先ディレクトリ")
    args = parser.parse_args()

    config = Config.from_env()
    if args.loops:
        config.max_research_loops = args.loops
    config.validate()

    topic = args.topic or console.input("[bold]調査タスクを入力してください: [/]").strip()
    if not topic:
        raise SystemExit("調査タスクが空です")

    console.print(Panel(f"{topic}\n[dim]model={config.llm_model}  loops={config.max_research_loops}[/]", title="調査開始"))

    with console.status("調査中..."):
        state = ResearchAgent(config, on_event=print_event).run(topic)

    report = build_report(state)
    console.rule("[bold]最終レポート")
    console.print(Markdown(report))

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w\-]+", "_", topic)[:40].strip("_")
    path = out_dir / f"{datetime.now():%Y%m%d_%H%M%S}_{slug}.md"
    path.write_text(report, encoding="utf-8")
    console.print(f"\n[bold green]レポートを保存しました:[/] {path}")


if __name__ == "__main__":
    main()
