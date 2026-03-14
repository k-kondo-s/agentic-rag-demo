# Agentic Search Demo

Pydantic AI + Chainlit + Tavily を使った、エージェンティック検索のデモアプリです。

AI エージェントがユーザーの質問に応じて **自律的に複数回のインターネット検索** を実行し、情報を統合して回答します。検索プロセスはリアルタイムでステップ表示されるので、エージェントの思考過程を確認できます。

## 技術スタック

| 技術 | 役割 |
|------|------|
| [Pydantic AI](https://ai.pydantic.dev/) | AI エージェントフレームワーク |
| [Chainlit](https://docs.chainlit.io/) | チャット UI・ストリーミング・認証 |
| [Tavily](https://tavily.com/) | インターネット検索 API |
| OpenAI GPT-4.1 | LLM |

## クイックスタート

```bash
# 1. 仮想環境を作成
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 環境変数を設定
cp .env.example .env
# .env を編集して API キーを入力

# 3. 認証シークレットを生成して .env に追記
chainlit create-secret

# 4. 起動
chainlit run app.py
```

ブラウザで http://localhost:8000 を開き、設定した ID/PW でログインしてください。

## 環境変数

| 変数 | 説明 | 取得方法 |
|------|------|---------|
| `OPENAI_API_KEY` | OpenAI API キー | [platform.openai.com](https://platform.openai.com/api-keys) |
| `TAVILY_API_KEY` | Tavily 検索 API キー | [tavily.com](https://tavily.com/) |
| `CHAINLIT_AUTH_SECRET` | 認証シークレット | `chainlit create-secret` で生成 |
| `APP_USERNAME` | ログイン ID | 任意（デフォルト: `demo`） |
| `APP_PASSWORD` | ログインパスワード | 任意 |

## Railway デプロイ

1. GitHub にリポジトリを push
2. [Railway](https://railway.app/) で新規プロジェクト → GitHub 連携
3. Dashboard の Variables で環境変数を設定
4. 自動ビルド・デプロイ

## ファイル構成

```
app.py             — メインアプリ（単一ファイルで完結）
chainlit.md        — Welcome メッセージ
.chainlit/         — Chainlit 設定
requirements.txt   — 依存関係
Dockerfile         — コンテナデプロイ用
.env.example       — 環境変数テンプレート
```
