from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import EventBusDep, SessionDep
from app.api.v1.schemas import MissionCreate, MissionDispatchRead, MissionRead
from app.db.base import Mission
from app.mqtt.outbound import MqttPublisher, get_mqtt_publisher
from app.services.mission_dispatch import MissionDispatchService
from app.services.mission_service import MissionService

router = APIRouter(prefix="/missions", tags=["missions"])
PublisherDep = Annotated[MqttPublisher, Depends(get_mqtt_publisher)]


@router.get("", response_model=list[MissionRead])
async def list_missions(session: SessionDep) -> list[Mission]:
    result = await session.execute(select(Mission).order_by(Mission.created_at))
    return list(result.scalars())


@router.get("/{mission_id}", response_model=MissionRead)
async def get_mission(mission_id: str, session: SessionDep) -> Mission:
    mission = await session.get(Mission, mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    return mission


@router.post("", response_model=MissionRead, status_code=status.HTTP_201_CREATED)
async def create_mission(
    payload: MissionCreate, session: SessionDep, event_bus: EventBusDep
) -> Mission:
    try:
        return await MissionService(session, event_bus).create_mission(
            payload.map_id,
            payload.start_node_key,
            payload.goal_node_key,
            payload.assigned_robot_id,
            payload.priority,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{mission_id}/dispatch",
    response_model=MissionDispatchRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def dispatch_mission(
    mission_id: str,
    session: SessionDep,
    publisher: PublisherDep,
    event_bus: EventBusDep,
) -> MissionDispatchRead:
    result = await MissionDispatchService(session, publisher, event_bus).dispatch_mission(
        mission_id
    )
    if not result.accepted:
        status_code = status.HTTP_404_NOT_FOUND if result.errors == ["Mission not found"] else 400
        raise HTTPException(status_code=status_code, detail=result.errors)
    return MissionDispatchRead(
        accepted=result.accepted,
        topic=result.topic,
        payload=result.payload,
        errors=result.errors,
    )
