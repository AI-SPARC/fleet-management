def on_connect(client, userdata, flags, rc):
    print(f"Connected to client {client} with result code {str(rc)}")
    # Aqui você pode adicionar qualquer lógica adicional necessária quando a conexão é estabelecida

def on_message(client, userdata, msg):
    print(f"Message received on topic {msg.topic}: {msg.payload.decode()}")
    # Aqui você pode processar a mensagem recebida (por exemplo, atualizar o status de um AGV)