"""A minimal agent that uses the tools on your MCP server.

Start your MCP server first:  python server/main.py
Then ask the agent a question:  python agent/main.py "Your question"
"""
import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from openai import OpenAI

load_dotenv()

SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")
MODEL = "gpt-5.4-mini"
MAX_STEPS = 8  # the most times the agent may call the LLM for one question
SYSTEM_PROMPT = (
    "You answer questions about a Neo4j knowledge graph. "
    "Use the tools to find the data, and answer only from what the tools return."
)

# The LLM runs through the workshop's LLM proxy, which uses the OpenAI API.
llm = OpenAI(base_url=os.environ["OPENAI_BASE_URL"], api_key=os.environ["OPENAI_API_KEY"])


# tag::agent_loop[]
async def ask(question: str) -> str:
    async with streamablehttp_client(SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # The tools on the server, described the way the LLM expects.
            # The LLM sees each tool's name, description, and parameters, and nothing else.
            tools = [ # (1)
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    }, # (2)
                }
                for tool in (await session.list_tools()).tools
            ]

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ]

            for _ in range(MAX_STEPS): # (3)
                # The LLM reasons about the question and the results so far
                reply = llm.chat.completions.create(
                    model=MODEL, messages=messages, tools=tools
                ).choices[0].message # (4)
                messages.append(reply)

                # No tool calls: the LLM has enough to answer
                if not reply.tool_calls:
                    return reply.content # (5)

                # Tool calls: run each one on the MCP server and give the LLM the result
                for call in reply.tool_calls:
                    arguments = json.loads(call.function.arguments)
                    print(f"Tool: {call.function.name} {arguments}")
                    result = await session.call_tool(call.function.name, arguments)
                    text = "\n".join(getattr(item, "text", "") for item in result.content)
                    messages.append( # (6)
                        {"role": "tool", "tool_call_id": call.id, "content": text}
                    )

            return "The agent stopped after too many steps."
# end::agent_loop[]


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or input("Question: ")
    print(f"\n{asyncio.run(ask(question))}")
