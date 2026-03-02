#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "DHT.h"
#define DHTPIN D4    
#define DHTTYPE DHT11  
 
// Initialize DHT sensor.
DHT dht(DHTPIN, DHTTYPE);
// Update these with values suitable for your network.

const char* ssid = "wifiname";
const char* password = "wifipassword";
const char* mqtt_server = "xxx.xxx.xxx.xxx";

// Initialize wifi & PubSub client
WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {

  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}


void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");

    if (client.connect("senseclient")) {
      Serial.println("connected");
      // Once connected, publish an announcement...
      
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(1000);
    }
  }
}

void setup() {
  
  Serial.begin(9600);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  dht.begin();
}
void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  delay(5000);
  DynamicJsonDocument doc(1024);
  JsonObject obj=doc.as<JsonObject>();
  float temp=dht.readTemperature();
  float humid=dht.readHumidity();
  doc["Temp"]= temp;
  doc["Humid"]= humid;
  char jsonStr[60];
  serializeJson(doc,jsonStr);
  Serial.print(jsonStr);
  Serial.println();
  client.publish("testing",jsonStr);
}
