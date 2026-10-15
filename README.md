# Neo4j MCP Server Workshop

Companion code for the [Neo4j MCP Server Workshop](https://graphacademy.neo4j.com/courses/workshop-mcp/) on GraphAcademy. In the workshop you build a knowledge graph for your own use case, then build an MCP server whose tools let an agent query it.

## Setup

[Open this repository in a GitHub Codespace](https://codespaces.new/neo4j-graphacademy/workshop-mcp)

**Or** set up on your own machine (Python 3.10 or later):

```bash
python -m venv .venv
source .venv/bin/activate    # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then fill in your values
python test_environment.py
```

Work entirely in the Codespace or entirely on your own machine. Do not mix the two, because the MCP server and the client need to run in the same place.

## Environment 

1. Fill in `.env` with the connection details from the course.
2. Run `python test_environment.py`. Every check should pass before you start.

## Run the MCP server and the test client

Start the server in one terminal. It listens on `http://localhost:8000/mcp`:

```bash
python server/main.py
```

Then, in a second terminal, run the test client to list the server's tools and call them:

```bash
python client/main.py          # pick a tool and call it
python client/main.py --list   # list the tools and exit
```

The server has two example tools, `get_schema` and `get_sample_nodes`. Add your own tools in `server/main.py`, below the marked comment, and restart the server after each change.

## Run the agent

With the MCP server running, ask the agent a question. It prints each tool it calls:

```bash
python agent/main.py "Which movies has Tom Hanks acted in?"
```

## The files

| File | What it is |
| --- | --- |
| `server/main.py` | The MCP server: the Neo4j connection, two example tools, and the place for your tools |
| `client/main.py` | A command-line client for testing the server |
| `agent/main.py` | A minimal Python agent that uses your server's tools |
| `solutions/` | A reference solution for the Movies graph |
| `my-tools/` | Where you record your questions, queries and tool definitions. Your coding agent reads it |
| `AGENTS.md` | Instructions for your coding agent. `.github/copilot-instructions.md` and `CLAUDE.md` point to it |
| `test_environment.py` | Checks your `.env`, the Neo4j connection, and the LLM connection |
| `.vscode/mcp.json` | Connects VS Code to the server |
