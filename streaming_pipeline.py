from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
import os

spark = SparkSession.builder \
    .appName("WeatherStreaming") \
    .config("spark.jars", "/opt/spark/jars/spark-sql-kafka-0-10_2.12-3.5.0.jar,/opt/spark/jars/postgresql-42.7.3.jar,/opt/spark/jars/kafka-clients-3.6.0.jar,/opt/spark/jars/spark-token-provider-kafka-0-10_2.12-3.5.0.jar") \
    .getOrCreate()

schema = StructType([
    StructField("city", StringType()),
    StructField("temperature_c", DoubleType()),
    StructField("humidity", DoubleType()),
    StructField("wind_speed_kph", DoubleType()),
    StructField("condition", StringType()),
    StructField("last_updated", StringType()),
    StructField("timestamp", StringType())
])

# Đọc KAFKA_BOOTSTRAP_SERVERS từ biến môi trường
kafka_bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", "weather_data") \
    .load()

df = df.select(from_json(col("value").cast("string"), schema).alias("weather")) \
       .select("weather.*")
df = df.withColumn("timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss"))

aggregated_df = df \
    .withWatermark("timestamp", "10 minutes") \
    .groupBy(window(col("timestamp"), "1 hour")) \
    .agg(
        avg("temperature_c").alias("avg_temp"),
        avg("humidity").alias("avg_humidity"),
        avg("wind_speed_kph").alias("avg_wind_speed")
    ) \
    .select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        col("avg_temp"),
        col("avg_humidity"),
        col("avg_wind_speed")
    )

def write_to_postgres(batch_df, batch_id):
    print(f"Batch {batch_id}:")
    if batch_df.count() > 0:
        batch_df.show()
        batch_df.write \
            .format("jdbc") \
            .option("url", os.getenv("JDBC_URL", "jdbc:postgresql://postgres-service:5432/weather_db")) \
            .option("dbtable", "weather_summary") \
            .option("user", os.getenv("JDBC_USER", "postgres")) \
            .option("driver", "org.postgresql.Driver") \
            .mode("append") \
            .save()
    else:
        print(f"Batch {batch_id}: No records to process")

query = aggregated_df.writeStream \
    .foreachBatch(write_to_postgres) \
    .outputMode("update") \
    .start()
query.awaitTermination()