from typing import Annotated

from fastapi import FastAPI, File, Response, UploadFile, Form
import httpx
import uvicorn

app = FastAPI()

s3_url = "http://storage-ms:8080/storage"


@app.post("/upload_file")
async def create_upload_file(file: UploadFile, username: str, path: str):

    contents = await file.read()
    filename = bytes(file.filename, encoding="utf-8")
    len_file = len(filename)

    len_name = len(username)
    len_path = len(path)

    content = len_name.to_bytes() + bytes(username, encoding="utf-8") + len_file.to_bytes() \
        + filename + len_path.to_bytes() + bytes(path, encoding="utf-8") + contents

    response = httpx.post(s3_url + "/upload",
                content=content)


@app.post("/add_permission")
async def add_permission(username: str, file: str, path: str):
    pass

@app.post("/download_file", responses={
    200: {
        "content": {"application/octet-stream": {}}
    }
})
async def download_file(username: str, filename: str, path: str) -> Response:


    response = httpx.post(s3_url + "/download",
                           json={"username": username, "filename": filename,
                                 "path": path})

    content_bytes = response.content

    return Response(content=content_bytes)



@app.post("/create_user")
async def create_user(username: str):
    response = httpx.post(s3_url + "/create_user",
                           json={"username": username})


@app.post("/delete_user")
async def delete_user(username: str):
    response = httpx.post(s3_url + "/delete_user",
                           json={"username": username})


@app.post("/list_files")
async def list_files(username: str):
    response = httpx.post(s3_url + "/list",
                           json={"username": username})



if __name__ == "__main__":
    uvicorn.run("main:app", port=8081, log_level="info")