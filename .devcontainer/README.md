# Setup

This repository accompanies the [Neo4j MCP Server Workshop](https://graphacademy.neo4j.com/courses/workshop-mcp/) on [GraphAcademy](https://graphacademy.neo4j.com).

When the devcontainer is created, such as in a GitHub Codespace, the required packages are installed and an `.env` file is created for you from [`.env.example`](../.env.example).

You will need to:

1. Update the values in the [`.env`](../.env) file with the connection details from the course.
2. Run [`test_environment.py`](../test_environment.py) to check the environment is set up correctly.

Work entirely in the Codespace or entirely on your own machine. Do not mix the two, because the MCP server and the client need to run in the same place.
