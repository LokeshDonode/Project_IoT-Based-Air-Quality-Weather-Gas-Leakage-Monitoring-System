"""
MQTT DHT Sensor Data Logger
Subscribes to MQTT topics and logs environmental sensor data.
"""

import logging
import os
from typing import Optional
from dataclasses import dataclass

import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error as MySQLError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', '192.168.1.56')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', 1883))
MQTT_TOPICS = ['temperature', 'humidity', 'pressure', 'altitude']

DB_CONFIG = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'dht_demo')
}

@dataclass
class SensorReading:
    """Represents a sensor reading from MQTT."""
    topic: str
    value: str
    unit: str

    def __str__(self) -> str:
        return f"{self.topic}: {self.value}{self.unit}"


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, config: dict):
        """
        Initialize database manager.
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self.connection = None

    def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection = mysql.connector.connect(**self.config)
            logger.info("Connected to database successfully")
            return True
        except MySQLError as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def insert_sensor_reading(self, table: str, value: float) -> bool:
        """
        Insert sensor reading into database.
        
        Args:
            table: Table name (e.g., 'temperature', 'humidity')
            value: Sensor value to insert
            
        Returns:
            True if insert successful, False otherwise
        """
        if not self.connection or not self.connection.is_connected():
            logger.warning("Database not connected, attempting reconnect")
            if not self.connect():
                return False

        try:
            cursor = self.connection.cursor()
            query = f"INSERT INTO {table} (value) VALUES (%s)"
            cursor.execute(query, (value,))
            self.connection.commit()
            cursor.close()
            logger.info(f"Inserted {value} into {table}")
            return True
        except MySQLError as e:
            logger.error(f"Failed to insert data: {e}")
            return False

    def close(self):
        """Close database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")


class MQTTSensorSubscriber:
    """Manages MQTT subscription and sensor data processing."""

    SENSOR_UNITS = {
        'temperature': '°C',
        'humidity': '%RH',
        'pressure': 'hPa',
        'altitude': 'm'
    }

    def __init__(self, broker_host: str, broker_port: int, db_manager: DatabaseManager):
        """
        Initialize MQTT subscriber.
        
        Args:
            broker_host: MQTT broker hostname/IP
            broker_port: MQTT broker port
            db_manager: DatabaseManager instance
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.db_manager = db_manager
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc: int) -> None:
        """
        Handle MQTT connection.
        
        Args:
            client: MQTT client instance
            userdata: User data
            flags: Connection flags
            rc: Connection result code
        """
        if rc == 0:
            logger.info("Connected to MQTT broker")
            for topic in MQTT_TOPICS:
                client.subscribe(topic)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Code: {rc}")

    def _on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
        """
        Handle incoming MQTT message.
        
        Args:
            client: MQTT client instance
            userdata: User data
            msg: MQTT message
        """
        try:
            # Decode payload
            payload = msg.payload.decode('utf-8')
            topic = msg.topic
            
            # Validate numeric value
            try:
                value = float(payload)
            except ValueError:
                logger.warning(f"Invalid numeric value received: {payload}")
                return

            # Get unit for this sensor
            unit = self.SENSOR_UNITS.get(topic, '')
            
            # Create sensor reading
            reading = SensorReading(topic=topic, value=payload, unit=unit)
            logger.info(f"Received: {reading}")
            
            # Store in database
            self.db_manager.insert_sensor_reading(topic, value)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def connect(self) -> bool:
        """
        Connect to MQTT broker.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    def start(self) -> None:
        """Start listening for MQTT messages."""
        if not self.connect():
            logger.error("Could not start subscriber: MQTT connection failed")
            return
            
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, disconnecting...")
        finally:
            self.disconnect()

    def disconnect(self) -> None:
        """Disconnect from MQTT broker and close database."""
        self.client.disconnect()
        self.db_manager.close()
        logger.info("Disconnected from MQTT broker")


def main():
    """Main entry point."""
    logger.info("Starting MQTT Sensor Subscriber")
    
    # Initialize database manager
    db_manager = DatabaseManager(DB_CONFIG)
    if not db_manager.connect():
        logger.error("Failed to initialize database connection")
        return

    # Initialize and start MQTT subscriber
    subscriber = MQTTSensorSubscriber(MQTT_BROKER_HOST, MQTT_BROKER_PORT, db_manager)
    subscriber.start()


if __name__ == '__main__':
    main()