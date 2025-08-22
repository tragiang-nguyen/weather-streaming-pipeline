# Sử dụng image cơ bản của Spark
FROM apache/spark:3.5.6-scala2.12-java17-ubuntu
# Cài đặt Python và các công cụ cần thiết
USER root
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*
# Sao chép file Python và JAR
COPY producer.py /app/
COPY streaming_pipeline.py /opt/spark/work-dir/
COPY jars/ /opt/spark/jars/
# Cài đặt thư viện Python
RUN pip3 install kafka-python requests
# Thiết lập môi trường
ENV SPARK_HOME=/opt/spark
ENV PATH=$PATH:$SPARK_HOME/bin
ENV SPARK_LOCAL_IP=0.0.0.0
ENV PYTHONPATH=$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.10.9.7-src.zip:$PYTHONPATH
# Cổng (nếu cần)
EXPOSE 4040
# Chạy producer.py với log, sau đó chạy spark-submit
CMD ["sh", "-c", "python3 /app/producer.py > /app/producer.log 2>&1 & sleep 5 && spark-submit --jars /opt/spark/jars/spark-sql-kafka-0-10_2.12-3.5.0.jar,/opt/spark/jars/postgresql-42.7.3.jar,/opt/spark/jars/kafka-clients-3.6.0.jar,/opt/spark/jars/spark-token-provider-kafka-0-10_2.12-3.5.0.jar /opt/spark/work-dir/streaming_pipeline.py"]