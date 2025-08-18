import json

from decouple import config

from kafka import KafkaProducer
from kafka.errors import KafkaError

from logger import setup_logger

logger = setup_logger()


# get environment variables
KAFKA_BROKER = config('KAFKA_BROKER')
KAFKA_TOPIC = config('KAFKA_TOPIC')

if not KAFKA_BROKER or not KAFKA_TOPIC:
    logger.error("KAFKA_BROKER and KAFKA_TOPIC must be set in the environment variables.")
    raise ValueError("KAFKA_BROKER and KAFKA_TOPIC must be set in the environment variables.")


logger.info("Starting Kafka producer setup...")


class MetricProducer:
    def __init__(self, broker, topic):
        self.broker = broker
        self.topic = topic
        
        self.producer = self.create_producer()
    
    def create_producer(self):
        """Creates and returns a Kafka producer instance."""
        try:
            producer = KafkaProducer(
                bootstrap_servers=[self.broker],
                value_serializer=lambda m: json.dumps(m).encode('ascii'),
                retries=5,  # Retry sending messages up to 5 times
                acks='all'  # Wait for all replicas to acknowledge the message
            )
            logger.info(f"Successfully connected to Kafka broker at {self.broker}")
            return producer
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka broker: {str(e)}")
            raise e

    def __str__(self):
        return json.dumps(self.data, indent=2)
    
    def __call__(self, message: dict, ):
        try:
            future = self.producer.send(self.topic, value=message)
            record_metadata = future.get(timeout=10)  # Wait for the send to complete
            
            logger.info(f"Message sent successfully to {self.topic}!")
            logger.info(f"  Topic: {record_metadata.topic}")
            logger.info(f"  Partition: {record_metadata.partition}")
            logger.info(f"  Offset: {record_metadata.offset}")
        except KafkaError as e:
            logger.error(f"Failed to send message to {self.topic} due to a Kafka error: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            raise e



dump_metrics = MetricProducer(broker=KAFKA_BROKER, topic=KAFKA_TOPIC)

