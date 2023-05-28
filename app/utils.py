from typing import Optional
from neo4j import GraphDatabase

class GraphConnector:
    def __init__(self,
                 uri: str = 'bolt://localhost:7687',
                 user: str = 'neo4j',
                 password: Optional[str] = None
                ):
        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password)
        )

    def close(self):
        self.driver.close()

    def query(self,
              query: str,
              parameters: Optional[dict] = None,
              database: Optional[str] = None,
              **kwargs
             ):
        assert self.driver is not None, "Driver needs to be initialized"
        response = None
        try:
            response = self.driver.execute_query(
                query,
                parameters=parameters,
                database=database,
                **kwargs
            )
        except Exception as err:
            print(f"ERROR: {err}")
        return response
