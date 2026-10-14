# Tests the environment: the .env file, the Neo4j connection, and the LLM connection.
# Run with: python test_environment.py
import os
import unittest

from dotenv import load_dotenv, find_dotenv
load_dotenv()


class TestEnvironment(unittest.TestCase):

    skip_env_variable_tests = True
    skip_neo4j_test = True
    skip_llm_test = True

    def test_env_file_exists(self):
        env_file_exists = True if find_dotenv() > "" else False
        if env_file_exists:
            TestEnvironment.skip_env_variable_tests = False
        self.assertTrue(env_file_exists, ".env file not found.")

    def env_variable_exists(self, variable_name):
        self.assertIsNotNone(
            os.getenv(variable_name),
            f"{variable_name} not found in .env file")

    def test_neo4j_variables(self):
        if TestEnvironment.skip_env_variable_tests:
            self.skipTest("Skipping Neo4j env variables test")

        self.env_variable_exists('NEO4J_URI')
        self.env_variable_exists('NEO4J_USERNAME')
        self.env_variable_exists('NEO4J_PASSWORD')
        self.env_variable_exists('NEO4J_DATABASE')

        for name in ('NEO4J_URI', 'NEO4J_PASSWORD', 'NEO4J_DATABASE'):
            value = os.getenv(name)
            self.assertFalse(
                value == "..." or "xxxxxxxx" in value,
                f"{name} in the .env file still has the example value. Replace it with the value from the course.")
        TestEnvironment.skip_neo4j_test = False

    def test_neo4j_connection(self):
        if TestEnvironment.skip_neo4j_test:
            self.skipTest("Skipping Neo4j connection test")

        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USERNAME'),
                  os.getenv('NEO4J_PASSWORD'))
        )
        try:
            # Run a query against the named database, so a wrong NEO4J_DATABASE
            # fails here and not later, inside the MCP server.
            driver.execute_query("RETURN 1 AS ok", database_=os.getenv('NEO4J_DATABASE'))
            connected = True
        except Exception:
            connected = False

        driver.close()

        self.assertTrue(
            connected,
            "Neo4j connection failed. Check the NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD "
            "and NEO4J_DATABASE values in the .env file."
        )

    def test_llm_variables(self):
        if TestEnvironment.skip_env_variable_tests:
            self.skipTest("Skipping LLM env variables test")

        self.env_variable_exists('OPENAI_API_KEY')
        self.env_variable_exists('OPENAI_BASE_URL')

        self.assertFalse(
            os.getenv('OPENAI_API_KEY') in ("", "...", "ga-..."),
            "OPENAI_API_KEY in the .env file still has the example value. Replace it with the API key from the course.")
        TestEnvironment.skip_llm_test = False

    def test_llm_connection(self):
        if TestEnvironment.skip_llm_test:
            self.skipTest("Skipping LLM connection test")

        from openai import OpenAI, AuthenticationError

        client = OpenAI(
            base_url=os.getenv('OPENAI_BASE_URL'),
            api_key=os.getenv('OPENAI_API_KEY'),
        )
        msg = None
        try:
            # The course's LLM service has no model list, so the test makes a very small request.
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Reply with the word OK."}],
                max_tokens=5,
            )
        except AuthenticationError:
            msg = "LLM authentication failed. Check the OPENAI_API_KEY value in the .env file."
        except Exception as e:
            msg = (
                "LLM connection failed. Check the OPENAI_BASE_URL value in the .env file, "
                f"and that you have enabled your AI access in the course. ({e})"
            )

        self.assertIsNone(msg, msg)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestEnvironment('test_env_file_exists'))
    suite.addTest(TestEnvironment('test_neo4j_variables'))
    suite.addTest(TestEnvironment('test_neo4j_connection'))
    suite.addTest(TestEnvironment('test_llm_variables'))
    suite.addTest(TestEnvironment('test_llm_connection'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
