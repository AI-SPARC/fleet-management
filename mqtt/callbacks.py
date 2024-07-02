from mqtt.handlers.handle_connection import handle_connection

topic_handlers = {
    "connection": handle_connection,
}

def on_connect(client, userdata, flags, rc):
    print(f"Connected to client {client} with result code {str(rc)}")

def on_message(client, userdata, msg):
    topic = msg.topic.split('/')[-1] 

    if topic in topic_handlers:
        handler_function = topic_handlers[topic]
        handler_function(client, userdata, msg)