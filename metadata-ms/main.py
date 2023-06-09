from fastapi import FastAPI, Response
import httpx
import uvicorn

from typing import List

from .cassandra_client import CassandraClient

app = FastAPI()

host = 'metadata-db'
port = 9042
keyspace = "metadata"
tables = ["files"]
params = ["filename", "owner", "users"]

client = CassandraClient(host, port, keyspace)
client.connect()

@app.post("/insert_file")
async def insert_file(username: str, filename: str):
    client.insert_data(tables[0], params, [filename, username, [username]])


@app.post("/give_permissions")
async def change_permissions(username: str, filename: str, users: List[str]):
    user_list = client.read_from_table(tables[0], ['users'],
                            f"WHERE owner = '{username}' AND filename = '{filename}'")

    l = [i for i in users if i not in user_list.one().users]
    for user in user_list.one().users:
        l.append(user)
    client.insert_data(tables[0], params, [filename, username, l])

@app.post("/remove_permissions")
async def change_permissions(username: str, filename: str, users: List[str]):
    user_list = client.read_from_table(tables[0], ['users'],
                            f"WHERE owner = '{username}' AND filename = '{filename}'")

    l = [i for i in user_list.one().users if i not in users]
    client.insert_data(tables[0], params, [filename, username, l])


@app.get("/get_permission_status")
async def get_permission_status(username: str, filename: str, user: str) -> bool:
    users = client.read_from_table(tables[0], ['users'],
                            f"WHERE owner = '{username}' AND filename = '{filename}'")
    row = users.one()
    if row:
        result = user in row[0]
        return result
    return False


@app.post("/show_table")
async def show_table():
    rows = client.read_from_table(tables[0], ['filename', 'owner', 'users'], "")
    return list(rows)

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8080, log_level="info")