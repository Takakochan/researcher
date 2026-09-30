import asyncio
import dataclasses
from pathlib import Path

import discord
from discord import app_commands

from .agent import ResearchAgent, build_report, save_report
from .config import Config
from .mailer import send_report

DISCORD_MESSAGE_LIMIT = 2000
EMBED_DESCRIPTION_LIMIT = 4096
REPORTS_DIR = Path("reports")


def truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


class ProgressLog:
    """調査の途中経過を 1 つの Discord メッセージに書き足していく"""

    def __init__(self, message: discord.Message, loop: asyncio.AbstractEventLoop):
        self.message = message
        self.loop = loop
        self.lines: list[str] = []

    def on_event(self, event: str, data: dict) -> None:
        # ResearchAgent は別スレッドで動くので、イベントループ側で編集を実行する
        if event == "query":
            self.lines.append(f"🔎 初期クエリ: {data['query']}")
        elif event == "loop_start":
            self.lines.append(f"\n**ループ {data['loop']}** — 検索: {data['query']}")
        elif event == "search":
            self.lines.extend(f"・<{r.url}>" for r in data["results"])
        elif event == "summary":
            self.lines.append("✅ 要約を更新")
        elif event == "reflection":
            self.lines.append(f"🤔 不足: {data['knowledge_gap']}")
        else:
            return
        text = "\n".join(self.lines)
        if len(text) > DISCORD_MESSAGE_LIMIT:  # 長くなったら新しい行を残す
            text = "…" + text[-(DISCORD_MESSAGE_LIMIT - 1):]
        future = asyncio.run_coroutine_threadsafe(self.message.edit(content=text), self.loop)
        try:
            future.result()
        except Exception as e:  # 途中経過の表示に失敗しても調査は続ける
            print(f"progress update failed: {e}")


class ResearchBot(discord.Client):
    def __init__(self, config: Config):
        super().__init__(intents=discord.Intents.default())
        self.config = config
        self.tree = app_commands.CommandTree(self)
        self.lock = asyncio.Lock()
        self._register_commands()

    async def setup_hook(self) -> None:
        if self.config.discord_guild_id:
            guild = discord.Object(id=self.config.discord_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} — /research で調査を依頼できます")

    def _register_commands(self) -> None:
        @self.tree.command(name="research", description="ウェブ調査を実行してレポートを作成します")
        @app_commands.describe(topic="調査タスク", loops="調査ループ回数（省略時は .env の設定）")
        @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
        async def research(
            interaction: discord.Interaction,
            topic: str,
            loops: app_commands.Range[int, 1, 10] | None = None,
        ) -> None:
            await self.handle_research(interaction, topic, loops)

    async def handle_research(
        self, interaction: discord.Interaction, topic: str, loops: int | None
    ) -> None:
        if interaction.user.id not in self.config.discord_allowed_user_ids:
            await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True)
            return

        config = dataclasses.replace(self.config)
        if loops:
            config.max_research_loops = loops

        waiting = self.lock.locked()
        await interaction.response.send_message(
            f"📝 **調査タスク:** {truncate(topic, 1500)}\n"
            + ("⏳ 他の調査が実行中です。終わり次第開始します。" if waiting else "🚀 調査を開始します…")
        )
        # interaction の応答トークンは 15 分で失効するため、以降はチャンネルに直接投稿する
        channel = interaction.channel

        async with self.lock:
            status = await channel.send("準備中…")
            progress = ProgressLog(status, asyncio.get_running_loop())
            try:
                agent = ResearchAgent(config, on_event=progress.on_event)
                state = await asyncio.to_thread(agent.run, topic)
                report = build_report(state)
                path = save_report(report, topic, REPORTS_DIR)
            except Exception as e:
                await channel.send(f"{interaction.user.mention} ❌ 調査中にエラーが発生しました: `{truncate(str(e), 1500)}`")
                return

            embed = discord.Embed(
                title=truncate(f"調査レポート: {topic}", 256),
                description=truncate(state.summary, EMBED_DESCRIPTION_LIMIT),
            )
            await channel.send(
                content=f"{interaction.user.mention} ✅ 調査が完了しました（全文は添付ファイル）",
                embed=embed,
                file=discord.File(path),
            )

            if config.mail_to:
                try:
                    await asyncio.to_thread(send_report, config, config.mail_to, f"調査レポート: {topic[:60]}", path)
                    await channel.send(f"📧 {config.mail_to} にメールで送信しました")
                except Exception as e:
                    await channel.send(f"⚠️ メール送信に失敗しました: `{truncate(str(e), 1500)}`")


def main() -> None:
    config = Config.from_env()
    config.validate()
    if not config.discord_bot_token:
        raise SystemExit(".env に DISCORD_BOT_TOKEN を設定してください")
    if not config.discord_allowed_user_ids:
        raise SystemExit(".env に DISCORD_ALLOWED_USER_IDS（実行を許可する Discord ユーザー ID）を設定してください")
    ResearchBot(config).run(config.discord_bot_token)


if __name__ == "__main__":
    main()
