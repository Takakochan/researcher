# Researcher

Token Factory（LLM）と Tavily（検索）を使った反復型ウェブリサーチツール。

1. 調査タスクから検索クエリを生成
2. Tavily で情報源を検索
3. 検索結果を LLM で要約（2 回目以降は既存の要約を更新）
4. 要約を振り返り、不足している知識を特定
5. 不足を補うための新しい検索クエリを生成

2〜5 を `MAX_RESEARCH_LOOPS` 回繰り返す。

## セットアップ

`.env` に `TOKEN_FACTORY_API_KEY` と `TAVILY_API_KEY` を記入してから:

```bash
uv sync
uv run researcher "調査したいテーマ"
uv run researcher -n 5 "調査したいテーマ"   # ループ回数を指定
uv run researcher                          # 対話入力
```

レポートは `reports/` に Markdown 形式で保存される。

## Windows でのインストール

1. リポジトリをクローン（または GitHub から ZIP をダウンロードして展開）
   ```powershell
   git clone https://github.com/Takakochan/researcher.git
   cd researcher
   ```
2. `install.bat` をダブルクリック（uv のインストール、依存関係のインストール、`.env` の作成を自動で行う）
3. 作成された `.env` をメモ帳などで開き、`TOKEN_FACTORY_API_KEY` と `TAVILY_API_KEY` を記入
4. 実行
   ```powershell
   .\research.bat "調査したいテーマ"
   .\research.bat -n 5 "調査したいテーマ"
   ```

改行を含む調査タスクを渡したい場合は、`research.bat` ではなく PowerShell から直接実行する
（`.bat` 経由だと改行以降が切れるため）:

```powershell
uv run researcher "1 行目
2 行目"
```

※ `$` やバッククォートを含む場合はシングルクォート `'...'` で囲む。

## レポートのメール送信

`.env` に `MAIL_TO` と SMTP 設定を記入すると、調査終了後にレポートを自動でメール送信する
（本文にレポート、`.md` ファイルを添付）。`MAIL_TO` が空なら送信しない。

Gmail の場合:
1. Google アカウントで 2 段階認証を有効にする
2. https://myaccount.google.com/apppasswords で「アプリ パスワード」を発行
3. `.env` に記入
   ```
   MAIL_TO=送信先@example.com
   SMTP_USER=自分のアドレス@gmail.com
   SMTP_PASSWORD=発行したアプリパスワード(16文字)
   ```

一時的に宛先を変える: `--mail-to other@example.com` / 送信しない: `--no-mail`

## Discord から実行する

Discord で `/research topic:調査タスク` と送ると調査を実行し、途中経過と最終レポート（ファイル添付）を投稿する。
`MAIL_TO` が設定されていればメールでも送信する。

### 初回セットアップ

1. https://discord.com/developers/applications で「New Application」を作成
2. 左メニュー「Bot」→「Reset Token」でトークンを発行し、`.env` の `DISCORD_BOT_TOKEN` に記入
3. 左メニュー「OAuth2」→「OAuth2 URL Generator」で
   - SCOPES: `bot` と `applications.commands` にチェック
   - BOT PERMISSIONS: `Send Messages`、`Attach Files`、`Embed Links`、`Read Message History` にチェック
   - 生成された URL をブラウザで開き、自分のサーバーにボットを招待
4. Discord の「設定 → 詳細設定 → 開発者モード」をオンにし、
   - 自分のアイコンを右クリック →「ユーザー ID をコピー」→ `.env` の `DISCORD_ALLOWED_USER_IDS` に記入
   - サーバー名を右クリック →「サーバー ID をコピー」→ `.env` の `DISCORD_GUILD_ID` に記入

### 起動

- Windows: `bot.bat` をダブルクリック（ウィンドウを開いている間だけ動作）
- Mac: `uv run researcher-bot`

`Logged in as ...` と表示されたら準備完了。サーバーのチャンネル、またはボットとの DM で `/research` を実行する。

### Windows 起動時に自動でボットを起動する

`Win + R` → `shell:startup` で開いたフォルダに、`bot.bat` のショートカットを置く。
