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
