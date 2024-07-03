from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from models.Connection import Connection
from models.Factsheet import Factsheet
from models.InstantActions import InstantActions
from models.Order import Order
from models.State import State
from api.handle_message import send_mqtt_message

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/{interface_name}/{major_version}/{manufacturer}/{serial_number}/order")
async def post_order_topic(interface_name: str, major_version: str, manufacturer: str, serial_number: str, data: Order):
    topic = f"{interface_name}/{major_version}/{manufacturer}/{serial_number}/order"
    return send_mqtt_message(topic, data)

@router.post("/{interface_name}/{major_version}/{manufacturer}/{serial_number}/instantActions")
async def post_instant_actions_topic(interface_name: str, major_version: str, manufacturer: str, serial_number: str, data: InstantActions):
    topic = f"{interface_name}/{major_version}/{manufacturer}/{serial_number}/instantActions"
    return send_mqtt_message(topic, data)

# Routes just for testing ==================================================================================
@router.post("/{interface_name}/{major_version}/{manufacturer}/{serial_number}/connection")
async def post_instant_actions_topic(interface_name: str, major_version: str, manufacturer: str, serial_number: str, data: Connection):
    topic = f"{interface_name}/{major_version}/{manufacturer}/{serial_number}/connection"
    return send_mqtt_message(topic, data)

@router.post("/{interface_name}/{major_version}/{manufacturer}/{serial_number}/factsheet")
async def post_instant_actions_topic(interface_name: str, major_version: str, manufacturer: str, serial_number: str, data: Factsheet):
    topic = f"{interface_name}/{major_version}/{manufacturer}/{serial_number}/factsheet"
    return send_mqtt_message(topic, data)

@router.post("/{interface_name}/{major_version}/{manufacturer}/{serial_number}/state")
async def post_instant_actions_topic(interface_name: str, major_version: str, manufacturer: str, serial_number: str, data: State):
    topic = f"{interface_name}/{major_version}/{manufacturer}/{serial_number}/state"
    return send_mqtt_message(topic, data)