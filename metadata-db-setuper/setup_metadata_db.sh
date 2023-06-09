#!/usr/bin/env bash

until printf "" 2>>/dev/null >>/dev/tcp/metadata-db/9042; do 
    sleep 3;
    echo "Waiting for cassandra...";
done

echo "Creating keyspace and table..."

cqlsh metadata-db -f /create_schema.cql
