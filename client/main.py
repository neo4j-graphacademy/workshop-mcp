"""A small command-line client for testing an MCP server.

It connects to the server, lists its tools, and lets you call one.

Run it with:  python client/main.py
List the tools and exit:  python client/main.py --list
"""
import asyncio
import json
import os
import sys
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")


def ask_for_arguments(input_schema: dict[str, Any]) -> dict[str, Any]:
    """Ask for a value for each of the tool's parameters."""
    arguments: dict[str, Any] = {}
    properties = input_schema.get("properties", {})
    required = input_schema.get("required", [])

    for name, details in properties.items():
        kind = details.get("type", "string")
        is_required = name in required
        label = "required" if is_required else "optional, press Enter to skip"
        print(f"\n{name} ({kind}, {label})")
        if details.get("description"):
            print(f"  {details['description']}")

        while True:
            text = input("  value: ").strip()
            if not text and not is_required:
                break
            if not text:
                print("  A value is required.")
                continue
            try:
                if kind == "integer":
                    arguments[name] = int(text)
                elif kind == "number":
                    arguments[name] = float(text)
                elif kind == "boolean":
                    arguments[name] = text.lower() in ("true", "yes", "y", "1")
                elif kind in ("object", "array"):
                    arguments[name] = json.loads(text)
                else:
                    arguments[name] = text
                break
            except ValueError as error:
                print(f"  Not a valid {kind}: {error}")
    return arguments


def print_tools(tools: list[Any]) -> None:
    for number, tool in enumerate(tools, start=1):
        print(f"\n{number}. {tool.name}")
        if tool.description:
            print(f"   {tool.description}")


def print_result(result: Any) -> None:
    for item in result.content:
        print(getattr(item, "text", item))
    if result.isError:
        print("\nThe tool returned an error.")


async def main() -> None:
    list_only = "--list" in sys.argv[1:]

    print(f"Connecting to {SERVER_URL}")
    async with streamablehttp_client(SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools

            if not tools:
                print("The server has no tools.")
                return

            print_tools(tools)
            if list_only:
                return

            while True:
                choice = input("\nTool number to call (Enter to quit): ").strip()
                if not choice:
                    return
                if not choice.isdigit() or not 1 <= int(choice) <= len(tools):
                    print("Enter one of the numbers above.")
                    continue

                tool = tools[int(choice) - 1]
                arguments = ask_for_arguments(tool.inputSchema)
                print(f"\nCalling {tool.name} with {json.dumps(arguments)}")
                try:
                    print_result(await session.call_tool(tool.name, arguments))
                except Exception as error:  # show the problem and let the learner try again
                    print(f"Call failed: {error}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as error:
        print(f"Could not talk to the server: {error}")
        print("Is the server running? Start it with: python server/main.py")
        sys.exit(1)
