import json
from config import mqtt_client
from typing import Union
from models.InstantActions import InstantActions
from models.Order import Order
from http.client import HTTPException
    
def send_mqtt_message(topic: str, data: Union[Order, InstantActions]) -> dict:
    try:
        msg = json.dumps(data.dict(), default=str)
        result = mqtt_client.publish(topic, msg)
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        return {
            "topic": topic,
            "status": status,
            "msg": msg,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send MQTT message: {str(e)}")