"""Agentic RAG Demo — Pydantic AI + Chainlit + Tavily"""

import os

import chainlit as cl
from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    ToolCallPart,
    ToolReturnPart,
)
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
        "回答は日本語で、出典（URL）があれば末尾にまとめてください。\n"
        "検索が不要な雑談や挨拶にはそのまま応答してください。"
    ),
)


@agent.tool_plain
async def search_web(query: str) -> str:
    """インターネットで情報を検索する。queryは検索キーワード（英語推奨）。"""
    response = tavily.search(query, max_results=5)
    results = response.get("results", [])
    if not results:
        return "検索結果が見つかりませんでした。"
    lines = []
    for r in results:
        lines.append(f"### {r['title']}")
        lines.append(r.get("content", ""))
        lines.append(f"URL: {r['url']}")
        lines.append("")
    return "\n".join(lines)


# --- Chainlit auth ---
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    expected_user = os.environ.get("APP_USERNAME", "demo")
    expected_pass = os.environ.get("APP_PASSWORD", "")
    if username == expected_user and password == expected_pass:
        return cl.User(identifier=username)
    return None


# --- Chainlit handlers ---
@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(
        content="こんにちは！何でも聞いてください。インターネットで検索してお答えします。"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    history = cl.user_session.get("history", [])

    # Streaming response
    msg = cl.Message(content="")
    await msg.send()

    async with agent.run_stream(
        message.content, message_history=history
    ) as result:
        async for chunk in result.stream_text(delta=True):
            await msg.stream_token(chunk)

    await msg.update()

    # Show tool calls as Steps
    for msg_item in result.new_messages():
        if isinstance(msg_item, ModelRequest):
            for part in msg_item.parts:
                if isinstance(part, ToolReturnPart):
                    async with cl.Step(
                        name=f"検索結果: {part.tool_name}",
                        type="tool",
                    ) as step:
                        step.output = (
                            part.content
                            if isinstance(part.content, str)
                            else str(part.content)
                        )
        elif isinstance(msg_item, ModelResponse):
            for part in msg_item.parts:
                if isinstance(part, ToolCallPart):
                    async with cl.Step(
                        name=f"🔍 {part.tool_name}",
                        type="tool",
                    ) as step:
                        args = part.args
                        if isinstance(args, dict):
                            step.input = args.get("query", str(args))
                        else:
                            step.input = str(args)

    # Persist history
    cl.user_session.set("history", result.all_messages())
