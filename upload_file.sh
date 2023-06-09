#!/bin/bash
# 
# Upload file to the cloud storage:
# ./upload_file.sh LOCAL_PATH_TO_FILE USERNAME SAVE_PATH

LOCAL_PATH_TO_FILE=$1
USERNAME=$2
SAVE_PATH=$3

curl -X 'POST' \
  'http://localhost:3000/upload_file' \
  --data-urlencode "username=${USERNAME}" \
  --data-urlencode "path=${SAVE_PATH}" \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F "file=@${LOCAL_PATH_TO_FILE};type=text/plain"
