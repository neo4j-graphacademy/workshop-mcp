# My tools

Define a tool for each question your knowledge graph needs to answer. Your coding agent reads this file when it builds the tools in `server/main.py`.

A tool is a Cypher query that an agent can call. The agent reads the tool's **description** to decide whether to use it, so write it for the agent, not for yourself.

Keep each query read-only (`MATCH`, `WHERE`, `RETURN`, `WITH`, `ORDER BY`, `LIMIT`), and write each value as a `$parameter`.

## Example

### movies_by_actor

- **Question:** Which movies has an actor appeared in?
- **Description:** Find the movies an actor has appeared in, with the role they played. Use it when the question is about a particular actor's films.
- **Parameters:**
  - `actor` (text, required): the actor's full name
  - `limit` (number, optional): the most movies to return, 10 by default
- **Query:**
  ```cypher
  MATCH (p:Person)-[r:ACTED_IN]->(m:Movie)
  WHERE p.name = $actor
  RETURN m.title AS movie, m.year AS year, r.role AS role
  ORDER BY m.year
  LIMIT $limit
  ```
- **Returns:** a list of movies, each with its title, year and the role

## Your tools

### (tool name)

- **Question:**
- **Description:**
- **Parameters:**
- **Query:**
  ```cypher
  ```
- **Returns:**

### (tool name)

- **Question:**
- **Description:**
- **Parameters:**
- **Query:**
  ```cypher
  ```
- **Returns:**
