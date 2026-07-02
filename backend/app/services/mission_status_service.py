from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Mission, MqttMessageLog
from app.services.event_bus import EventBus, get_event_bus


class MissionStatusService:
    def __init__(self, session: AsyncSession, event_bus: EventBus | None = None) -> None:
        self.session = session
        self.event_bus = event_bus or get_event_bus()

    async def reconcile(self, robot_id: str, payload: dict[str, Any]) -> Mission | None:
        mission = await self._resolve_mission(robot_id, payload)
        if mission is None or mission.status in {"completed", "failed", "canceled"}:
            return mission

        next_status = infer_mission_status(mission, payload)
        if await self._cancel_action_finished(robot_id, payload):
            next_status = "canceled"
        if next_status == mission.status:
            return mission

        previous_status = mission.status
        mission.status = next_status
        await self.session.commit()
        await self.session.refresh(mission)
        self.event_bus.publish(
            "mission.status.changed",
            robot_id=robot_id,
            mission_id=mission.id,
            payload={"status": next_status, "previousStatus": previous_status},
        )
        return mission

    async def _resolve_mission(
        self, robot_id: str, payload: dict[str, Any]
    ) -> Mission | None:
        order_id = payload.get("orderId")
        if isinstance(order_id, str) and order_id:
            mission = await self.session.get(Mission, order_id)
            if mission is not None and mission.assigned_robot_id == robot_id:
                return mission
            return None
        result = await self.session.execute(
            select(Mission)
            .where(
                Mission.assigned_robot_id == robot_id,
                Mission.status.in_(["sent", "running"]),
            )
            .order_by(Mission.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _cancel_action_finished(
        self, robot_id: str, payload: dict[str, Any]
    ) -> bool:
        finished_ids = {
            state.get("actionId")
            for state in (payload.get("actionStates") or [])
            + (payload.get("instantActionStates") or [])
            if state.get("actionStatus") == "FINISHED"
        }
        if not finished_ids:
            return False
        logs = (
            await self.session.execute(
                select(MqttMessageLog.payload).where(
                    MqttMessageLog.robot_id == robot_id,
                    MqttMessageLog.direction == "outbound",
                    MqttMessageLog.message_type == "instantActions",
                )
            )
        ).scalars()
        return any(
            action.get("actionId") in finished_ids and action.get("actionType") == "cancelOrder"
            for log_payload in logs
            for action in log_payload.get("actions") or []
        )


def infer_mission_status(mission: Mission, payload: dict[str, Any]) -> str:
    if any(error.get("errorLevel") == "FATAL" for error in payload.get("errors") or []):
        return "failed"
    at_goal = payload.get("lastNodeId") == mission.goal_node_key
    route_consumed = not (payload.get("nodeStates") or []) and not (
        payload.get("edgeStates") or []
    )
    if at_goal and route_consumed and payload.get("driving") is not True:
        return "completed"
    if payload.get("orderId") == mission.id and mission.status in {"assigned", "sent"}:
        return "running"
    return mission.status
