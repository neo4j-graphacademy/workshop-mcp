"""An MCP server that gives an agent access to your Neo4j knowledge graph.

Run it with:  python server/main.py
It listens on http://localhost:8000/mcp
"""
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP
from neo4j import AsyncDriver, AsyncGraphDatabase, RoutingControl

load_dotenv()


@dataclass
class AppContext:
    """What every tool can reach: the Neo4j driver and the database to query."""

    driver: AsyncDriver
    database: str


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Open the Neo4j connection when the server starts and close it when it stops."""
    uri = os.environ["NEO4J_URI"]
    username = os.environ["NEO4J_USERNAME"]
    password = os.environ["NEO4J_PASSWORD"]
    # There is no default: the database is named after your instance, not "neo4j".
    database = os.environ["NEO4J_DATABASE"]

    driver = AsyncGraphDatabase.driver(uri, auth=(username, password))
    try:
        yield AppContext(driver=driver, database=database)
    finally:
        await driver.close()


mcp = FastMCP("Workshop MCP Server", lifespan=app_lifespan)


def to_json(value: Any) -> Any:
    """Turn Neo4j values, such as dates and points, into values an MCP response can carry."""
    if isinstance(value, dict):
        return {key: to_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


async def read(ctx: Context, cypher: str, **parameters: Any) -> list[dict[str, Any]]:
    """Run a read-only query and return each row as a dictionary."""
    app: AppContext = ctx.request_context.lifespan_context
    records, _, _ = await app.driver.execute_query(
        cypher,
        parameters,
        database_=app.database,
        routing_=RoutingControl.READ,
    )
    return [to_json(record.data()) for record in records]


# ---------------------------------------------------------------------------
# Example tools. The docstring is the description the agent reads to decide
# when to call the tool, and the parameters become the tool's inputs.
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_schema(ctx: Context) -> dict[str, Any]:
    """Get the schema of the knowledge graph: its node labels with their properties,
    and the relationships that connect them. Call this first to learn what the graph contains."""
    nodes = await read(
        ctx,
        """
        CALL db.schema.nodeTypeProperties()
        YIELD nodeLabels, propertyName
        UNWIND nodeLabels AS label
        WITH label, collect(DISTINCT propertyName) AS properties
        RETURN label, [p IN properties WHERE p IS NOT NULL] AS properties
        ORDER BY label
        """,
    )
    relationships = await read(
        ctx,
        """
        CALL db.schema.visualization()
        YIELD relationships
        UNWIND relationships AS rel
        RETURN DISTINCT startNode(rel).name AS from, type(rel) AS type, endNode(rel).name AS to
        ORDER BY type
        """,
    )
    return {"nodes": nodes, "relationships": relationships}


MAX_SAMPLE = 25
MAX_TEXT = 200
MAX_LIST = 20


def shorten(value: Any) -> Any:
    """Shorten long text and long lists, such as embeddings, so a result does not flood the agent."""
    if isinstance(value, dict):
        return {key: shorten(item) for key, item in value.items()}
    if isinstance(value, list):
        if len(value) > MAX_LIST:
            return f"[a list of {len(value)} items]"
        return [shorten(item) for item in value]
    if isinstance(value, str) and len(value) > MAX_TEXT:
        return value[:MAX_TEXT] + "..."
    return value


@mcp.tool()
async def get_sample_nodes(ctx: Context, label: str, limit: int = 5) -> list[dict[str, Any]]:
    """Get a sample of nodes that have the given label, with all of their properties.
    It returns some of the nodes, not all of them. Use get_schema to see the labels."""
    labels = [row["label"] for row in await read(ctx, "CALL db.labels() YIELD label RETURN label")]
    if label not in labels:
        return [{"error": f"Unknown label '{label}'. The labels in this graph are: {', '.join(labels)}"}]

    # A label cannot be a query parameter, so it is checked against the real labels
    # above and then written into the query with backticks.
    safe_label = label.replace("`", "")
    rows = await read(
        ctx,
        f"""
        MATCH (n:`{safe_label}`)
        RETURN properties(n) AS properties
        LIMIT $limit
        """,
        limit=max(1, min(limit, MAX_SAMPLE)),
    )
    return [shorten(row["properties"]) for row in rows]


# ---------------------------------------------------------------------------
# YOUR TOOLS GO HERE
#
# Add a tool for each question your knowledge graph needs to answer:
#
#   @mcp.tool()
#   async def my_tool(ctx: Context, some_input: str) -> list[dict[str, Any]]:
#       """Describe what the tool does and when an agent should use it."""
#       return await read(ctx, "MATCH ... WHERE ... = $some_input RETURN ...", some_input=some_input)
#
# Restart the server after you change a tool.
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
