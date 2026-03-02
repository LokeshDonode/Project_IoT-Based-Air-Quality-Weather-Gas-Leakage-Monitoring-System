from multiprocessing.dummy import connection
import flask
import paho.mqtt.client
import mysql.connector
import paho.mqtt.subscribe as subscribe


def insert_temp_mysql(query):
    mysql.connector.connect(
        user="root",
        password="manager",
        host="localhost",
        database="weather"
    )
    cursor = connection.cursor()
    cursor.execute(query)
    result= cursor.fetchall()
    cursor.close()
    connection.commit()
    connection.close()

    return result

def on_connect(client,user_data,flag,rc):
    client.subscribe('temperature')
    client.subscribe('humidity')
    client.subscribe('pressure')
    client.subscribe('altitude')


def on_message(client,user_data,message):
    
    
    msg = subscribe.simple("temperature", hostname="192.168.1.56")
    print("%s %s°C" % (msg.topic, msg.payload))
    print()
    msg1 = subscribe.simple("humidity", hostname="192.168.1.56")
    print("%s %sRH" % (msg1.topic, msg1.payload))
    print()
    msg2 = subscribe.simple("pressure", hostname="192.168.1.56")
    print("%s %shPa" % (msg2.topic, msg2.payload))
    print()
    msg3 = subscribe.simple("altitude", hostname="192.168.1.56")
    print("%s %sm" % (msg3.topic, msg3.payload))
    print()
    
    
    
    temp = msg.payload.decode('utf-8')
    hum = msg1.payload.decode('utf-8')
    pres = msg.payload.decode('utf-8')
    alt = msg.payload.decode('utf-8')


    query=f"insert into bmp280(temperature,humidity,pressure,altitude) values(temp,hum,pres,alt));"
    insert_temp_mysql(query)
    #return DHT

client = paho.mqtt.client.Client()

client.on_connect = on_connect

client.on_message = on_message


client.connect('192.168.1.56')

client.loop_forever()