from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from api.models.__all_models import Connection, Factsheet, InstantActions, Order, State, Visualization
from api.handle_message import send_mqtt_message

router = APIRouter()
router.mount("/static", StaticFiles(directory="api/static"), name="static")
templates = Jinja2Templates(directory="api/templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/order", response_class=HTMLResponse)
async def publish_order_template(request: Request):
    return templates.TemplateResponse("publish_order.html", {"request": request})

@router.get("/nodes", response_class=HTMLResponse)
async def nodes_template(request: Request):
    return templates.TemplateResponse("create_nodes.html", {"request": request})

@router.get("/edges", response_class=HTMLResponse)
async def edges_template(request: Request):
    return templates.TemplateResponse("create_edges.html", {"request": request})

@router.get("/actions", response_class=HTMLResponse)
async def actions_template(request: Request):
    return templates.TemplateResponse("create_actions.html", {"request": request})

@router.get("/digital_twin", response_class=HTMLResponse)
async def digital_twin_template(request: Request):
    return templates.TemplateResponse("digital_twin.html", {"request": request})

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