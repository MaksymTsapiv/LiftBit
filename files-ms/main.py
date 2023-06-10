from typing import Annotated, List

from fastapi import FastAPI, File, Response, UploadFile, Form
import httpx
import uvicorn

from .analytics import KafkaClient

s3_url =    "http://storage-ms:8080/storage"
meta_url =  "http://metadata-ms:80"
KAFKA_HOST = "kafka-broker"

types = {
    "png":     "image/png",
    "jpg":     "image/jpg",
    "txt":     "text/plain",
    "html":    "text/html"
}

app = FastAPI()
analytics_client = KafkaClient(KAFKA_HOST)

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
    
    httpx.post(meta_url + "/insert_file",
                         params={"username": username, "filename": file.filename})    

    analytics_client.log_upload(username, path, file.size)


@app.post("/change_permissions")
async def add_permission(username: str, filename: str,
                          give: List[str]=[], remove: List[str]=[]):
    if give:
        httpx.post(meta_url + "/give_permissions",
                            params={"username": username, "filename": filename},
                            json=give)

    if remove:
        httpx.post(meta_url + "/remove_permissions",
                            params={"username": username, "filename": filename},
                            json=remove)

@app.post("/download_file", responses={
    200: {
        "content": {"application/octet-stream": {}}
    }
})
async def download_file(username: str, filename: str, path: str,
                         owner: str) -> Response:
    
    end = filename.split('.')[-1]
    media_type = types[end] if filename != end else types["txt"]

    access = httpx.get(meta_url + "/get_permission_status",
                         params={"username": owner, "filename": filename,
                               "user": username})

    if (access.json()):
        response = httpx.post(s3_url + "/download",
                            json={"username": username, "filename": filename,
                                    "path": path})

        content_bytes = response.content

        analytics_client.log_download(owner, path, len(content_bytes), username)

        return Response(content=content_bytes, media_type=media_type)
    return Response(status_code=403)



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
    return Response(content=response.content, media_type="text/plain")



if __name__ == "__main__":
    uvicorn.run("main:app", port=8081, log_level="info")