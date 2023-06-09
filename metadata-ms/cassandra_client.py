from cassandra.cluster import Cluster
from typing import List

class CassandraClient:
    def __init__(self, host, port, keyspace):
        self.host = host
        self.port = port
        self.keyspace = keyspace
        self.session = None

    def connect(self):
        cluster = Cluster([self.host], port=self.port)
        self.session = cluster.connect(self.keyspace)

    def execute(self, query):
        self.session.execute(query)

    def close(self):
        self.session.shutdown()
    
    def read_from_table(self, table_name, params, conditions):
        procesed_params = str(params)[1:-1].replace("'", "", -1)
        query = f"SELECT {procesed_params} FROM {table_name} {conditions}"
        rows = self.session.execute(query)
        return rows

    def insert_data(self, table, params: List, values: List):
        procesed_params = str(params)[1:-1].replace("'", "", -1)
        procesed_values = str(values)[1:-1].replace('"', "'", -1)
        query = f"INSERT INTO {table} ({procesed_params}) VALUES ({procesed_values})"
        self.execute(query)
        # return query
