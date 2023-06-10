#!/usr/bin/env bash

echo "Creating topic..."

export KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper-server:2181

kafka-topics.sh --create --bootstrap-server kafka-broker:9092 --replication-factor 1 --partitions 3 --topic file-events
