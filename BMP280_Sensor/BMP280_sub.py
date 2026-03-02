"""
BMP280 Sensor - MQTT to MySQL subscriber
Handles temperature, humidity, pressure, and altitude data from IoT sensors
"""

import logging
import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error
from typing import Optional, Dict
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', '192.168.1.56')
MQTT_TOPICS = ['temperature', 'humidity', 'pressure', 'altitude']
MQTT_QOS = 1

DB_CONFIG = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'weather'),
    'autocommit': True,
    'connection_timeout': 5
}

# Store the latest message from each topic
sensor_data = {
    'temperature': None,
    'humidity': None,
    'pressure': None,
    'altitude': None
}


class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.connection = None
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            logger.info("Database connected successfully")
            return True
        except Error as e:
            logger.error(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
    
    def insert_sensor_data(self, temperature: float, humidity: float, 
                          pressure: float, altitude: float) -> bool:
        """Insert sensor data into database with parameterized queries"""
        if not self.connection or not self.connection.is_connected():
            logger.error("Database not connected")
            return False
        
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO bmp280 (temperature, humidity, pressure, altitude) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (temperature, humidity, pressure, altitude))
            self.connection.commit()
            cursor.close()
            logger.info(f"Data inserted: Temp={temperature}°C, Humidity={humidity}%, "
                       f"Pressure={pressure}hPa, Altitude={altitude}m")
            return True
        except Error as e:
            logger.error(f"Database insert error: {e}")
            self.connection.rollback()
            return False


class MQTTSubscriber:
    """Handles MQTT subscription and message processing"""
    
    def __init__(self, broker: str, topics: list, db_manager: DatabaseManager):
        self.broker = broker
        self.topics = topics
        self.db = db_manager
        self.client = mqtt.Client(client_id="BMP280_subscriber")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, user_data, flags, rc):
        """Callback when client connects to broker"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            for topic in self.topics:
                client.subscribe(topic, qos=MQTT_QOS)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect, return code {rc}")
    
    def on_disconnect(self, client, user_data, rc):
        """Callback when client disconnects from broker"""
        if rc != 0:
            logger.warning(f"Unexpected disconnection: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def on_message(self, client, user_data, msg):
        """Callback when message is received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Store the latest value for each topic
            sensor_data[topic] = payload
            logger.debug(f"Received - Topic: {topic}, Value: {payload}")
            
            # Print current sensor readings
            self._print_sensor_data()
            
            # If all data is available, insert to database
            if all(sensor_data.values()):
                self._process_sensor_data()
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _print_sensor_data(self):
        """Print current sensor data"""
        units = {
            'temperature': '°C',
            'humidity': '%RH',
            'pressure': 'hPa',
            'altitude': 'm'
        }
        
        for topic, value in sensor_data.items():
            if value is not None:
                print(f"{topic}: {value}{units[topic]}")
    
    def _process_sensor_data(self):
        """Process and insert sensor data when all values are available"""
        try:
            temp = float(sensor_data['temperature'])
            humidity = float(sensor_data['humidity'])
            pressure = float(sensor_data['pressure'])
            altitude = float(sensor_data['altitude'])
            
            self.db.insert_sensor_data(temp, humidity, pressure, altitude)
        
        except ValueError as e:
            logger.error(f"Invalid sensor data format: {e}")
    
    def start(self):
        """Connect to MQTT broker and start listening"""
        try:
            self.client.connect(self.broker, port=1883, keepalive=60)
            logger.info(f"Connecting to MQTT broker at {self.broker}")
            self.client.loop_forever()
        except Exception as e:
            logger.error(f"Failed to start MQTT subscriber: {e}")
    
    def stop(self):
        """Stop the MQTT subscriber"""
        self.client.disconnect()
        self.client.loop_stop()


def main():
    """Main entry point"""
    db_manager = DatabaseManager(DB_CONFIG)
    
    if not db_manager.connect():
        logger.error("Failed to connect to database")
        return
    
    subscriber = MQTTSubscriber(MQTT_BROKER, MQTT_TOPICS, db_manager)
    
    try:
        subscriber.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        subscriber.stop()
    finally:
        db_manager.disconnect()


if __name__ == "__main__":
    main()
