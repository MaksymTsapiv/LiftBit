from typing import List
import string
import hashlib

from fastapi import (
    FastAPI, 
    Response, 
    UploadFile, 
    HTTPException,
    status
    )
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

# Allowed characters in names of files or directories
ALLOWED_CHARS = string.ascii_lowercase \
                + string.ascii_uppercase \
                + string.digits \
                + " ."

def check_validity(path: str):
    """Raises 404 HTTPException if has invalid characters
    """
    if not all(char in ALLOWED_CHARS for char in path):
        detail = "Forbidden character occured in path"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    parts = path.split('/')
    for part in parts:
        for char in part:
            if char not in ALLOWED_CHARS:
                detail = f"Forbitten character in path: {char}"
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

def check_username_validity(username: str):
    if not (1 <= len(username) <= 32):
        detail = "Username must be of size between 1 and 32 characters"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def hash_username(username: str):
    hash_obj = hashlib.sha256(username.encode()).hexdigest()
    return (username + hash_obj)[:63]

def check_user_exist(username: str): #TODO
    """Check if user exist
    """
    pass

@app.post("/upload_file")
async def upload_file(file: UploadFile, username: str, filename: str):
    check_user_exist(username)
    check_validity(filename)

    contents = await file.read()

    username_for_storage = hash_username(username)
    len_username = len(username_for_storage)
    len_path = len(filename)

    content = len_username.to_bytes() + bytes(username_for_storage, encoding="utf-8") \
        + len_path.to_bytes() + bytes(filename, encoding="utf-8") \
        + contents

    response = httpx.post(s3_url + "/upload",
                content=content)
    
    httpx.post(meta_url + "/insert_file",
                         params={"username": username, "filename": file.filename})    

    analytics_client.log_upload(username, filename, file.size)


@app.post("/give_permission")
async def give_permission(username: str, filename: str,
                          other_username: str):
    httpx.post(meta_url + "/give_permissions",
                        params={"username": username, "filename": filename},
                        json=[other_username])

@app.post("/remove_permission")
async def remove_permission(username: str, filename: str, other_username: str):
    httpx.post(meta_url + "/remove_permissions",
                        params={"username": username, "filename": filename},
                        json=[other_username])

@app.post("/download_file", responses={
    200: {
        "content": {"application/octet-stream": {}}
    }
})
async def download_file(username: str, path: str, owner: str) -> Response:
    # access = httpx.get(meta_url + "/get_permission_status",
    #                      params={"username": owner, "filename": filename,
    #                            "user": username})

    # if (access.json()):
    username_for_storage = hash_username(username)
    response = httpx.post(s3_url + "/download",
                        json={"username": username_for_storage, "path": path})

    content_bytes = response.content

    analytics_client.log_download(owner, path, len(content_bytes), username)

    return Response(content=content_bytes)
    # return Response(status_code=403)



@app.post("/create_user")
async def create_user(username: str):
    check_username_validity(username)
    username_for_storage = hash_username(username)
    response = httpx.post(s3_url + "/create_user",
                           json={"username": username_for_storage})


@app.post("/delete_user")
async def delete_user(username: str):
    username_for_storage = hash_username(username)
    response = httpx.post(s3_url + "/delete_user",
                           json={"username": username_for_storage})


@app.post("/delete_file")
async def delete_file(username: str, filename: str):
    check_validity(filename)
    username_for_storage = hash_username(username)
    response = httpx.post(s3_url + "/delete",
                           json={"username": username_for_storage,
                                 "path": filename})


@app.post("/list_files")
async def list_files(username: str):
    username_for_storage = hash_username(username)
    response = httpx.post(s3_url + "/list",
                           json={"username": username_for_storage})
    return Response(content=response.content, media_type="text/plain")



if __name__ == "__main__":
    uvicorn.run("main:app", port=8081, log_level="info")