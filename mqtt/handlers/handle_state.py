import json
from pydantic import ValidationError
from api.models.Connection import Connection

def handle_connection(client, userdata, msg):
    payload_str = msg.payload.decode()
    print(f"Handling connection message: {payload_str}")

    try:
        payload_dict = json.loads(payload_str)
        connection_data = Connection(**payload_dict)
        
        if connection_data.connectionState == "ONLINE":
            print("AGV is ONLINE. Connection is active.")
            
        elif connection_data.connectionState == "OFFLINE":
            print("AGV is OFFLINE. Connection ended in a coordinated way.")
            
        elif connection_data.connectionState == "CONNECTIONBROKEN":
            print("AGV connection is broken. Connection ended unexpectedly.")

    except ValidationError as e:
        print(f"Failed to validate the connection message: {e}")
        
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
