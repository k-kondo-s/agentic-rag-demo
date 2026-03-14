"""Agentic RAG Demo — Pydantic AI + Chainlit + Tavily"""

import os

import chainlit as cl
from pydantic_ai import Agent
from tavily import TavilyClient

# --- Tavily client ---
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# --- Pydantic AI Agent ---
agent = Agent(
    model="openai:gpt-4.1",
    system_prompt=(
        "あなたはインターネット検索ができるAIアシスタントです。\n"
        "ユーザーの質問に対して、必要に応じて search_web ツールを使い、"
        "最新の情報を調べてから回答してください。\n"
        "複数の観点が必要な場合は、異なるキーワードで複数回検索してください。\n"
        "回答は日本語で、出典（URL）があれば末尾にまとめてください。\n"
        "検索が不要な雑談や挨拶にはそのまま応答してください。"
    ),
)


@agent.tool_plain
async def search_web(query: str) -> str:
    """インターネットで情報を検索する。queryは検索キーワード（英語推奨）。"""
    async with cl.Step(name=f"🔍 検索: {query}", type="tool") as step:
        step.input = f"検索クエリ: `{query}`"
        response = tavily.search(query, max_results=5)
        results = response.get("results", [])
        if not results:
            step.output = "検索結果なし"
            return "検索結果が見つかりませんでした。"
        lines = []
        for r in results:
            lines.append(f"### {r['title']}")
            lines.append(r.get("content", ""))
            lines.append(f"URL: {r['url']}")
            lines.append("")
        output = "\n".join(lines)
        step.output = f"{len(results)} 件の結果を取得"
    return output


# --- Chainlit auth ---
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    expected_user = os.environ.get("APP_USERNAME", "demo")
    expected_pass = os.environ.get("APP_PASSWORD", "")
    if username == expected_user and password == expected_pass:
        return cl.User(identifier=username)
    return None


# --- Chainlit handlers ---
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="競合比較レポート",
            message="Pydantic AI と LangChain と LlamaIndex を比較して、それぞれの最新バージョンの特徴・長所・短所をまとめてください。",
        ),
        cl.Starter(
            label="最新トレンド深掘り",
            message="2025年のAIエージェント分野の最新トレンドを調べて、特に注目すべき技術やフレームワークを3つ挙げて詳しく解説してください。",
        ),
        cl.Starter(
            label="技術選定リサーチ",
            message="RAGシステムを構築する際のベクトルDBについて、Pinecone・Weaviate・Qdrant・Chromaの最新情報を調べて比較表を作ってください。",
        ),
        cl.Starter(
            label="ニュース横断検索",
            message="直近のOpenAI・Google・Anthropicそれぞれの最新ニュースを調べて、各社の動向をまとめてください。",
        ),
    ]


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])


@cl.on_message
async def on_message(message: cl.Message):
    history = cl.user_session.get("history", [])

    msg = cl.Message(content="")
    await msg.send()

    async with agent.run_stream(
        message.content, message_history=history
    ) as result:
        async for chunk in result.stream_text(delta=True):
            await msg.stream_token(chunk)

    await msg.update()
    cl.user_session.set("history", result.all_messages())
