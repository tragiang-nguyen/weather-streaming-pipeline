import pytest
from unittest.mock import Mock, patch, call
from pyspark.sql.types import StringType, DoubleType

class TestStreaming:
    def test_schema_structure(self):
        # Import schema inside test to avoid execution
        from streaming_pipeline import schema
        
        # Test schema fields
        assert len(schema.fields) == 7
        assert schema.fields[0].name == "city"
        assert schema.fields[0].dataType == StringType()
        assert schema.fields[1].name == "temperature_c"
        assert schema.fields[1].dataType == DoubleType()
        assert schema.fields[6].name == "timestamp"
        assert schema.fields[6].dataType == StringType()

    @patch('pyspark.sql.SparkSession.builder.getOrCreate')  # Global patch for Spark
    def test_write_to_postgres(self, mock_spark):
        # Mock Spark session
        mock_session = Mock()
        mock_spark.return_value = mock_session

        # Import function inside test to avoid execution
        from streaming_pipeline import write_to_postgres

        # Mock batch_df (configure chain calls)
        mock_batch_df = Mock()
        mock_batch_df.count.return_value = 1  # Count > 0
        mock_batch_df.show.return_value = None  # Show returns None
        mock_batch_df.cache.return_value = mock_batch_df  # Cache returns self

        # Mock write chain: write.format().option()... .mode().save()
        mock_write = mock_batch_df.write
        mock_format = Mock()
        mock_option1 = Mock()
        mock_option2 = Mock()
        mock_option3 = Mock()
        mock_option4 = Mock()
        mock_mode = Mock()
        mock_save = Mock()
        mock_save.return_value = None

        mock_write.format.return_value = mock_format
        mock_format.option.return_value = mock_option1
        mock_option1.option.return_value = mock_option2
        mock_option2.option.return_value = mock_option3
        mock_option3.option.return_value = mock_option4
        mock_option4.mode.return_value = mock_mode
        mock_mode.save.return_value = mock_save

        # Call function
        write_to_postgres(mock_batch_df, batch_id=1)

        # Assertions (check chain calls)
        mock_batch_df.show.assert_called_once()
        mock_batch_df.cache.assert_called_once()
        mock_batch_df.count.assert_called_once()  # Called for if condition

        # Check write chain
        mock_write.format.assert_called_once_with("jdbc")
        mock_format.option.assert_called_once_with("url", "jdbc:postgresql://postgres-service:5432/weather_db")
        mock_option1.option.assert_called_once_with("dbtable", "weather_summary")
        mock_option2.option.assert_called_once_with("user", "postgres")
        mock_option3.option.assert_called_once_with("driver", "org.postgresql.Driver")
        mock_option4.mode.assert_called_once_with("append")
        mock_mode.save.assert_called_once()

        mock_batch_df.unpersist.assert_called_once()