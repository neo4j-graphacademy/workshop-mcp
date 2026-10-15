# Lightweight tests for the server, the client, and the agent.
# They need no Neo4j instance and no LLM, so they are quick to run.
# Run with: python test_workshop.py
import asyncio
import contextlib
import importlib.util
import io
import logging
import os
import socket
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

import uvicorn
from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).parent

# Keep the output to the test results
logging.getLogger("mcp").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# The files are all named main.py, so each one is loaded from its path.
# The server and the agent read their settings when they are loaded, so
# example values are used when the .env file has none.
for name, value in {
    "NEO4J_URI": "bolt://localhost:7687",
    "NEO4J_USERNAME": "neo4j",
    "NEO4J_PASSWORD": "password",
    "NEO4J_DATABASE": "neo4j",
    "OPENAI_API_KEY": "test-key",
    "OPENAI_BASE_URL": "http://localhost:1/v1",
}.items():
    os.environ.setdefault(name, value)


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


server = load("workshop_server", "server/main.py")
client = load("workshop_client", "client/main.py")
agent = load("workshop_agent", "agent/main.py")


class TestServer(unittest.TestCase):

    def test_example_tools_are_registered(self):
        tools = asyncio.run(server.mcp.list_tools())
        names = [tool.name for tool in tools]
        self.assertIn("get_schema", names)
        self.assertIn("get_sample_nodes", names)

    def test_tools_have_descriptions(self):
        for tool in asyncio.run(server.mcp.list_tools()):
            self.assertTrue(tool.description, f"{tool.name} has no description")

    def test_to_json_makes_values_plain(self):
        self.assertEqual(server.to_json({"a": [1, object]})["a"][0], 1)
        self.assertIsInstance(server.to_json({"a": object})["a"], str)


class TestClient(unittest.TestCase):

    def printed(self, result) -> str:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            client.print_result(result)
        return output.getvalue()

    def test_prints_the_text_of_each_block(self):
        result = SimpleNamespace(content=[SimpleNamespace(text="one"), SimpleNamespace(text="two")], isError=False)
        self.assertEqual(self.printed(result), "one\ntwo\n")

    def test_prints_none_when_there_is_no_content(self):
        self.assertEqual(self.printed(SimpleNamespace(content=[], isError=False)), "None\n")

    def test_reports_an_error(self):
        result = SimpleNamespace(content=[SimpleNamespace(text="boom")], isError=True)
        self.assertIn("The tool returned an error.", self.printed(result))


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextlib.contextmanager
def example_server():
    """Serve a small MCP server with one tool, on a free port, for the agent to use."""
    mcp = FastMCP("Test server")

    @mcp.tool()
    def echo(text: str) -> str:
        """Return the text that was sent."""
        return text

    port = free_port()
    config = uvicorn.Config(mcp.streamable_http_app(), host="127.0.0.1", port=port, log_level="error")
    http_server = uvicorn.Server(config)
    thread = threading.Thread(target=http_server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not http_server.started and time.time() < deadline:
        time.sleep(0.05)
    try:
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        http_server.should_exit = True
        thread.join(timeout=5)


class FakeLlm:
    """Stands in for the LLM: asks for the echo tool, then answers with the tool's result."""

    def __init__(self, always_call_tools: bool = False):
        self.always_call_tools = always_call_tools
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, model, messages, tools):
        self.requests.append({"model": model, "messages": list(messages), "tools": tools})
        last = messages[-1]
        if not self.always_call_tools and isinstance(last, dict) and last["role"] == "tool":
            message = SimpleNamespace(content=f"The tool said: {last['content']}", tool_calls=None)
        else:
            call = SimpleNamespace(
                id="call_1",
                function=SimpleNamespace(name="echo", arguments='{"text": "hello"}'),
            )
            message = SimpleNamespace(content=None, tool_calls=[call])
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class TestAgent(unittest.TestCase):

    def ask(self, llm: FakeLlm, url: str) -> str:
        agent.SERVER_URL = url
        agent.llm = llm
        with contextlib.redirect_stdout(io.StringIO()):
            return asyncio.run(agent.ask("Say hello"))

    def test_calls_the_tool_and_answers_from_the_result(self):
        llm = FakeLlm()
        with example_server() as url:
            answer = self.ask(llm, url)

        self.assertEqual(answer, "The tool said: hello")
        # The LLM is given the server's tools, with their descriptions and parameters
        tool = llm.requests[0]["tools"][0]["function"]
        self.assertEqual(tool["name"], "echo")
        self.assertEqual(tool["description"], "Return the text that was sent.")
        self.assertIn("text", tool["parameters"]["properties"])
        # The second request carries the question, the tool call, and the tool's result
        roles = [m["role"] if isinstance(m, dict) else "assistant" for m in llm.requests[1]["messages"]]
        self.assertEqual(roles, ["system", "user", "assistant", "tool"])

    def test_stops_after_the_most_steps(self):
        llm = FakeLlm(always_call_tools=True)
        original = agent.MAX_STEPS
        agent.MAX_STEPS = 2
        try:
            with example_server() as url:
                answer = self.ask(llm, url)
        finally:
            agent.MAX_STEPS = original

        self.assertEqual(answer, "The agent stopped after too many steps.")
        self.assertEqual(len(llm.requests), 2)


if __name__ == "__main__":
    unittest.main()
