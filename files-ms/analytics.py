import json
from datetime import datetime

from kafka import KafkaProducer

TOPIC_NAME = 'file-events'

class KafkaClient:
    def __init__(self, kafka_host):
        self._producer = KafkaProducer(
            bootstrap_servers=kafka_host,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
        )

    def log_download(self, owner_username: str, path: str, size_bytes: int, downloader_username: str):
        info = {
            "owner_username": owner_username,
            "path": path,
            "size_bytes": size_bytes,
            "downloader_username": downloader_username
        }
        value = {
            'type': 'download',
            'info': json.dumps(info),
            'timestamp': datetime.now()
        }
        self._producer.send(topic=TOPIC_NAME, value=value)

    def log_upload(self, owner_username: str, path: str, size_bytes: int):
        info = {
            "owner_username": owner_username,
            "path": path,
            "size_bytes": size_bytes,
        }
        value = {
            'type': 'upload',
            'info': json.dumps(info),
            'timestamp': datetime.now()
        }
        self._producer.send(topic=TOPIC_NAME, value=value)
