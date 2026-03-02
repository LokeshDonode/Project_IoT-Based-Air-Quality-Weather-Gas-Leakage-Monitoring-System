#include <ESP8266WiFi.h>
#include <ArduinoMqttClient.h>
#include <ThingSpeak.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BMP280.h>

#define SEALEVELPRESSURE_HPA (1013.25)

// Initialize sensor.
Adafruit_BMP280 bmp;
float temperature, humidity, pressure, altitude;

// Initialize wifi & Mqtt client
WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

// Update these with values suitable for your network.
const char *ssid = "SUNBEAM";
const char *password = "1234567890";
// Mqtt Broker connection
const char broker[] = "192.168.0.104";
int port = 1883;
const char topic1[] = "Temperature";
const char topic2[] = "Pressure";
const char topic3[] = "Altitude";
// Thingspeak
int p, q, r ,s;
unsigned long myChannelNumber = 1854519 ;
const char *myWriteAPIKey = "CA5KNJ71LUAT8319";

// set interval for sending messages (milliseconds)
const long interval = 5000;
unsigned long previousMillis = 0;

void setup()
{

  Serial.begin(115200);
  // Connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  ThingSpeak.begin(wifiClient); // Initialize ThingSpeak

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP Address : ");
  Serial.println(WiFi.localIP()); // WiFi IP Address

  // Loop until we're reconnected
  Serial.print("Attempting to connect to the MQTT broker: ");
  Serial.println(broker);

  if (!mqttClient.connect(broker, port))
  {
    Serial.print("MQTT connection failed! Error code = ");
    Serial.println(mqttClient.connectError());
    while (1)
      ;
  }
  Serial.println("You're connected to the MQTT broker!");
  Serial.println();

  // BMP sensor Initialisation
  bmp.begin(0x76);

  // set the message receive callback
  mqttClient.onMessage(onMqttMessage);

  Serial.print("Subscribing to topic: ");
  // Serial.println(topic);
  Serial.println();

  // subscribe to a topic
  mqttClient.subscribe(topic1);
  mqttClient.subscribe(topic2);
  mqttClient.subscribe(topic3);

  // topics can be unsubscribed using:
  // mqttClient.unsubscribe(topic);

  Serial.print("Topic1: ");
  Serial.println(topic1);
  Serial.print("Topic2: ");
  Serial.println(topic2);
  Serial.print("Topic3: ");
  Serial.println(topic3);

  Serial.println();
}
void loop()
{

  temperature = bmp.readTemperature();
  pressure = bmp.readPressure() / 100.0F;
  altitude = bmp.readAltitude(SEALEVELPRESSURE_HPA);

  Serial.print("Temperature = ");
  Serial.print(bmp.readTemperature());
  Serial.println(" °C");

  Serial.print("Pressure = ");
  Serial.print(bmp.readPressure() / 100.0F);
  Serial.println(" hPa");

  Serial.print("Altitude = ");
  Serial.print(bmp.readAltitude(SEALEVELPRESSURE_HPA));
  Serial.println(" m");

  mqttClient.poll();
  Serial.println();
  delay(1000);

  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval)
  {
    // save the last time a message was sent
    previousMillis = currentMillis;

    // send message, the Print interface can be used to set the message contents
    mqttClient.beginMessage(topic1);
    mqttClient.print(temperature);
    mqttClient.endMessage();

    mqttClient.beginMessage(topic2);
    mqttClient.print(pressure);
    mqttClient.endMessage();

    mqttClient.beginMessage(topic3);
    mqttClient.print(altitude);
    mqttClient.endMessage();

    Serial.println();
  }
  // Write to ThingSpeak
  p = ThingSpeak.writeField(myChannelNumber, 1, temperature, myWriteAPIKey);
  q = ThingSpeak.writeField(myChannelNumber, 2, pressure, myWriteAPIKey);
  r = ThingSpeak.writeField(myChannelNumber, 3, altitude, myWriteAPIKey);
  s = ThingSpeak.writeField(myChannelNumber, 4, humidity, myWriteAPIKey);

}

void onMqttMessage(int messageSize)
{

  char message[messageSize];
  for (int index = 0; index < messageSize; index++)
  {
    message[index] = (char)mqttClient.read();
  }
  Serial.println();
  // Serial.println();
}