#!/bin/bash

sleep 10

# spark-submit --conf spark.jars.ivy=/analytics --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0 --master spark://spark-master:7077 --deploy-mode client main.py
cd /opt/app
spark-submit --conf spark.jars.ivy=/opt/app --packages "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0" --master spark://spark-master:7077 --deploy-mode client streaming_processing.py
