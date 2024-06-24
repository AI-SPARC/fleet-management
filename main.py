from fastapi import FastAPI
from api.routes import router
import config

app = FastAPI()
app.include_router(router)

mqtt_client = config.create_mqtt_client()

@app.on_event("startup")
async def startup_event():
    import threading
    mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
    mqtt_thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)