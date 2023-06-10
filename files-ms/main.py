from typing import Annotated, List

from fastapi import FastAPI, File, Response, UploadFile, Form
import httpx
import uvicorn

app = FastAPI()

s3_url =    "http://storage-ms:8080/storage"
meta_url =  "http://metadata-ms:80"


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


@app.post("/change_permissions")
async def add_permission(username: str, filename: str,
                          give: List[str], remove: List[str]):

    httpx.post(meta_url + "/give_permissions",
                         params={"username": username, "filename": filename, "users": give})    
    
    httpx.post(meta_url + "/remove_permissions",
                         params={"username": username, "filename": filename, "users": remove})    
    

@app.post("/download_file", responses={
    200: {
        "content": {"application/octet-stream": {}}
    }
})
async def download_file(username: str, filename: str, path: str,
                         owner: str) -> Response:

    access = httpx.get(meta_url + "/get_permission_status",
                         params={"username": owner, "filename": filename,
                               "user": username})

    if (access.json()):
        response = httpx.post(s3_url + "/download",
                            json={"username": username, "filename": filename,
                                    "path": path})

        content_bytes = response.content

        return Response(content=content_bytes, media_type="image/png")
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



if __name__ == "__main__":
    uvicorn.run("main:app", port=8081, log_level="info")