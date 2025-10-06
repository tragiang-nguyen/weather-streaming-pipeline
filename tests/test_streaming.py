import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql.functions import to_timestamp, col, window, avg

def test_timestamp_conversion():
    spark = SparkSession.builder \
        .appName("Test") \
        .master("local[*]") \
        .config("spark.eventLog.enabled", "false") \
        .config("spark.hadoop.fs.defaultFS", "file:///") \
        .getOrCreate()
    data = [("Hanoi", 25.0, 94, 6.1, "Mist", "2025-08-27 22:00", "2025-08-27 15:14:59")]
    df = spark.createDataFrame(data, ["city", "temperature_c", "humidity", "wind_speed_kph", "condition", "last_updated", "timestamp"])
    df_with_timestamp = df.withColumn("timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss"))
    assert df_with_timestamp.count() == 1
    assert df_with_timestamp.filter(col("timestamp").isNotNull()).count() == 1

def test_aggregation():
    spark = SparkSession.builder \
        .appName("Test") \
        .master("local[*]") \
        .config("spark.eventLog.enabled", "false") \
        .config("spark.hadoop.fs.defaultFS", "file:///") \
        .getOrCreate()
    data = [("Hanoi", 25.0, 94, 6.1, "Mist", "2025-08-27 22:00", "2025-08-27 15:14:59")]
    df = spark.createDataFrame(data, ["city", "temperature_c", "humidity", "wind_speed_kph", "condition", "last_updated", "timestamp"])
    df_with_timestamp = df.withColumn("timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss"))
    aggregated = df_with_timestamp.groupBy(window(col("timestamp"), "1 hour")).agg(avg("temperature_c").alias("avg_temp"))
    assert aggregated.count() == 1
    assert aggregated.filter(col("avg_temp").isNotNull()).count() == 1