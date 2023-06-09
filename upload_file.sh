#!/bin/bash
# 
# Upload file to the cloud storage:
# ./upload_file.sh LOCAL_PATH_TO_FILE USERNAME SAVE_PATH

LOCAL_PATH_TO_FILE=$1
USERNAME=$2
SAVE_PATH=$3

function url_encode() {
    echo "$@" \
    | sed \
        -e 's/%/%25/g' \
        -e 's/ /%20/g' \
        -e 's/!/%21/g' \
        -e 's/"/%22/g' \
        -e "s/'/%27/g" \
        -e 's/#/%23/g' \
        -e 's/(/%28/g' \
        -e 's/)/%29/g' \
        -e 's/+/%2b/g' \
        -e 's/,/%2c/g' \
        -e 's/-/%2d/g' \
        -e 's/:/%3a/g' \
        -e 's/;/%3b/g' \
        -e 's/?/%3f/g' \
        -e 's/@/%40/g' \
        -e 's/\$/%24/g' \
        -e 's/\&/%26/g' \
        -e 's/\*/%2a/g' \
        -e 's/\./%2e/g' \
        -e 's/\//%2f/g' \
        -e 's/\[/%5b/g' \
        -e 's/\\/%5c/g' \
        -e 's/\]/%5d/g' \
        -e 's/\^/%5e/g' \
        -e 's/_/%5f/g' \
        -e 's/`/%60/g' \
        -e 's/{/%7b/g' \
        -e 's/|/%7c/g' \
        -e 's/}/%7d/g' \
        -e 's/~/%7e/g'
}

curl -X 'POST' \
  "http://localhost:3000/upload_file?username=$(url_encode "$USERNAME")&path=$(url_encode "$SAVE_PATH")" \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F "file=@${LOCAL_PATH_TO_FILE};type=text/plain"
