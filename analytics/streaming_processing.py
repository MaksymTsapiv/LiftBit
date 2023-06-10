from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, LongType, TimestampType, StringType
from pyspark.sql import functions as F


KAFKA_BOOTSTRAP_SERVERS = "kafka-broker:9092"
KAFKA_TOPIC = "file-events"
FILE_PATH = "/data/AGOSTO_2022_PARQUET_FINAL/"


MAIN_SCHEMA = StructType([
    StructField("type", StringType()),
    StructField("info", StringType()),
    StructField("timestamp", TimestampType()),
])

DOWNLOAD_SCHEMA = StructType([
    StructField("owner_username", StringType()),
    StructField("path", StringType()),
    StructField("size_bytes", LongType()),
    StructField("downloader_username", StringType()),
])

UPLOAD_SCHEMA = StructType([
    StructField("owner_username", StringType()),
    StructField("path", StringType()),
    StructField("size_bytes", LongType()),
])


def main():
    spark = SparkSession.builder.appName("analytics").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    streaming_processing(spark)


def streaming_processing(spark: SparkSession):
    df_stream = spark\
        .readStream.format("kafka")\
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)\
        .option("subscribe", KAFKA_TOPIC)\
        .option("startingOffsets", "earliest")\
        .load()

    df_stream = df_stream.select(
        F.from_json(
            F.decode(F.col("value"), "utf-8"),
            MAIN_SCHEMA
        ).alias("value")
    ).select("value.*")

    download_info = df_stream.where(F.col("type") == "download").withColumn(
        "info",
        F.from_json(
            F.decode(F.col("info"), "utf-8"),
            DOWNLOAD_SCHEMA
        )
    ).select("timestamp", "info.*")

    download_statistics = download_info.groupBy(F.window("timestamp", "5 minutes"))\
        .agg(
            F.count(F.col("path")).alias("Number of downloads"),
            F.sum(F.col("size_bytes")).alias("Total size (in bytes)")
        )

    download_statistics.writeStream\
        .option("truncate", "false")\
        .outputMode("update")\
        .format("console")\
        .start()\
        .awaitTermination()

    # output_format = "csv"  # or "parquet", "json", etc.

    # download_statistics.writeStream\
    #     .option("truncate", "false")\
    #     .outputMode("update")\
    #     .format(output_format)\
    #     .option("path", "/analytics/analytics.csv")\
    #     .start()\
    #     .awaitTermination()

if __name__ == "__main__":
    main()
