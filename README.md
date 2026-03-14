# Agentic RAG Demo

Pydantic AI + Chainlit + Tavily を使った、エージェンティック検索のデモアプリです。

AI エージェントがユーザーの質問に応じてインターネットを検索し、最新の情報をもとに回答します。ツールの呼び出し過程が UI 上で可視化されるので、エージェントがどう考えて検索しているかを確認できます。

## 技術スタック

- **[Pydantic AI](https://ai.pydantic.dev/)** — AI エージェントフレームワーク
- **[Chainlit](https://docs.chainlit.io/)** — チャット UI（ストリーミング・ツールコール可視化・認証）
- **[Tavily](https://tavily.com/)** — インターネット検索 API
- **OpenAI GPT-4.1** — LLM

## セットアップ

### 1. 仮想環境の作成

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example` をコピーして `.env` を作成し、API キーを設定してください。

```bash
cp .env.example .env
```

| 変数 | 説明 |
|------|------|
| `OPENAI_API_KEY` | OpenAI の API キー |
| `TAVILY_API_KEY` | Tavily の API キー（[tavily.com](https://tavily.com/) で取得） |
| `CHAINLIT_AUTH_SECRET` | Chainlit の認証シークレット（下記コマンドで生成） |
| `APP_USERNAME` | ログイン用ユーザー名（デフォルト: `demo`） |
| `APP_PASSWORD` | ログイン用パスワード |

認証シークレットの生成:

```bash
chainlit create-secret
```

### 3. 起動

```bash
chainlit run app.py
```

ブラウザで `http://localhost:8000` を開き、設定した ID/PW でログインしてください。

## Railway へのデプロイ

1. このリポジトリを GitHub に push する
2. [Railway](https://railway.app/) で新規プロジェクトを作成し、GitHub リポジトリと連携
3. Railway Dashboard の Variables で環境変数を設定
4. 自動でビルド・デプロイされる

Railway では `PORT` 環境変数が自動設定されます。Dockerfile では `8080` を指定していますが、Railway 側で適宜マッピングされます。

## 構成

```
app.py          — メインアプリ（単一ファイル）
chainlit.md     — Welcome メッセージ
requirements.txt
Dockerfile      — Railway デプロイ用
.env.example    — 環境変数テンプレート
```

アプリは `app.py` 1 ファイルで完結しています。コードリーディングやカスタマイズが簡単です。
