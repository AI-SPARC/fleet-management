import threading
import signal
import sys
from fastapi import FastAPI
from api.routes import router
from config import mqtt_client
from contextlib import asynccontextmanager

app = FastAPI()
app.include_router(router)

mqtt_thread = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_thread
    mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
    mqtt_thread.start()
    
    yield

    mqtt_client.loop_stop()
    mqtt_thread.join()

app.router.lifespan_context = lifespan

def signal_handler(sig, frame):
    print("Stopping MQTT client...")
    mqtt_client.loop_stop()
    mqtt_thread.join()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)