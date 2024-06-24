import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from mqtt.topic_manager import subscribe_topics
from mqtt.callbacks import on_connect, on_message

load_dotenv()
BROKER_ADDRESS = os.getenv('BROKER_ADDRESS')

def create_mqtt_client():
    client = mqtt.Client()
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect(BROKER_ADDRESS, 1883, 60)
    
    for topic in subscribe_topics:
        client.subscribe(topic)
    
    return client