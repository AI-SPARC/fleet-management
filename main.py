import asyncio
import signal
import sys
from fastapi import FastAPI
from api.routes import router
from config import mqtt_client
from contextlib import asynccontextmanager

app = FastAPI()
app.include_router(router)

mqtt_task = None

async def mqtt_loop():
    while True:
        mqtt_client.loop()
        await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mqtt_task
    mqtt_task = asyncio.create_task(mqtt_loop())
    
    yield

    mqtt_task.cancel()
    try:
        await mqtt_task
    except asyncio.CancelledError:
        pass

app.router.lifespan_context = lifespan

def signal_handler(sig, frame):
    print("Stopping MQTT client...")
    mqtt_client.loop_stop()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
