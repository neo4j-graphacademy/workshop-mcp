# Neo4j MCP Server Workshop

This repository is the code for a workshop. The learner is building an MCP server that gives an AI agent access to their own Neo4j knowledge graph. They work out the questions their graph should answer, write a Cypher query for each, and turn each query into an MCP tool.

You are the coding agent that helps with the implementation. The learner makes the decisions.

## The repository

- `server/main.py` is the MCP server (FastMCP, streamable HTTP on port 8000). It has the Neo4j connection, a `read()` helper, two example tools, and a marked place for the learner's tools.
- `client/main.py` is a command-line client for testing the server's tools.
- `agent/main.py` is a minimal Python agent that uses the server's tools through an LLM.
- `solutions/` holds a reference solution for the Movies graph. Do not copy from it to build the learner's tools, as the learner decides their own tools.
- `my-tools/tools.md` holds the learner's tool definitions: for each tool, its question, name, description, parameters, the Cypher query it runs, and what it returns.
- `.vscode/mcp.json` connects VS Code to the server at `http://localhost:8000/mcp`.
- `.env` holds the Neo4j connection details. Never print it, commit it, or copy its values into code.

Read `my-tools/tools.md` before you write or change a tool.

## How to help

- The learner decides which tools to build, what to call them, and how to describe them. If `my-tools/tools.md` does not define a tool yet, ask the learner for the question it answers, its name, its description, and its parameters. Do not invent them.
- Build the tools that are defined. Keep each tool small and focused on one question.
- Explain what you changed in a sentence or two, so the learner understands the code.
- When something fails, help the learner find the cause. Point to the most likely cause first, and avoid rewriting working code.
- Work through the learner's problems with them. A hint is often more useful than the finished answer.

## Adding a tool

Add each tool in `server/main.py`, below the comment `YOUR TOOLS GO HERE`. Do not change the scaffold above it.

```python
@mcp.tool()
async def movies_by_actor(ctx: Context, actor: str, limit: int = 10) -> list[dict[str, Any]]:
    """Find the movies an actor has appeared in, with the role they played.
    Use it when the question is about a particular actor's films."""
    return await read(
        ctx,
        """
        MATCH (p:Person)-[r:ACTED_IN]->(m:Movie)
        WHERE p.name = $actor
        RETURN m.title AS movie, m.year AS year, r.role AS role
        ORDER BY m.year
        LIMIT $limit
        """,
        actor=actor,
        limit=limit,
    )
```

- **Parameters.** Give each parameter a type that matches its definition: `str` for text, `int` for a whole number, and `float` for a decimal number. Pass every value to the query as a `$parameter`. Never build a value into the Cypher text with string formatting. Labels and relationship types cannot be parameters, so check them against the real ones, as `get_sample_nodes` does.
- **Read-only.** Use only read clauses such as `MATCH`, `WHERE`, `RETURN`, `WITH`, `ORDER BY`, and `LIMIT`. Never `CREATE`, `MERGE`, `SET`, `DELETE`, or `REMOVE`. The `read()` helper runs queries in read mode.
- **Database.** Always run queries through `read()`. It uses the `NEO4J_DATABASE` value, which is not `neo4j`. Never hard-code a database name.
- **Description.** The docstring is what an agent reads to decide whether to call the tool. Say what the tool does, what it returns, and when to use it.
- **Results.** Return properties as columns, not whole nodes. Return plain values such as a `list[dict]` or a `dict`. Put a `LIMIT` on any query that could return many rows. Use `to_json()` if a value is not plain, such as a date.
- **Aggregates.** Return properties beside an aggregate, for example `RETURN p.name, count(m) AS movies`. Never `RETURN p, count(m)`.

## Running and testing

- Start the server with `python server/main.py`. It listens on `http://localhost:8000/mcp`.
- The server does not reload. Restart it after every change to a tool.
- Test the tools with `python client/main.py`. Use `python client/main.py --list` to list them.
- Check the environment with `python test_environment.py`.
- Run the quick tests of the server, client, and agent with `python test_workshop.py`. They need no Neo4j instance or LLM.
- A tool that returns a list sends one result block for each item. That is normal.

## Do not

- Do not write to the database.
- Do not change the server to use stdio. It uses streamable HTTP so it works in a Codespace.
- Do not add packages that are not in `requirements.txt` without asking the learner.
- Do not mix environments. The learner works entirely in a Codespace or entirely on their own machine.
