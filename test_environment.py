# Tests the environment: the .env file and the Neo4j connection.
# Run with: python test_environment.py
import os
import unittest

from dotenv import load_dotenv, find_dotenv
load_dotenv()


class TestEnvironment(unittest.TestCase):

    skip_env_variable_tests = True
    skip_neo4j_test = True

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


def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestEnvironment('test_env_file_exists'))
    suite.addTest(TestEnvironment('test_neo4j_variables'))
    suite.addTest(TestEnvironment('test_neo4j_connection'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
