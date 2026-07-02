from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Robot, RobotStateSnapshot
from app.services.event_bus import EventBus, get_event_bus
from app.services.mission_status_service import MissionStatusService


class RobotRegistryService:
    def __init__(self, session: AsyncSession, event_bus: EventBus | None = None) -> None:
        self.session = session
        self.event_bus = event_bus or get_event_bus()

    async def get_or_create(
        self, manufacturer: str, serial_number: str, display_name: str | None = None
    ) -> Robot:
        result = await self.session.execute(
            select(Robot).where(
                Robot.manufacturer == manufacturer,
                Robot.serial_number == serial_number,
            )
        )
        robot = result.scalar_one_or_none()
        if robot is not None:
            if display_name and robot.display_name != display_name:
                robot.display_name = display_name
                await self._touch_and_commit(robot)
            return robot

        robot = Robot(
            manufacturer=manufacturer,
            serial_number=serial_number,
            display_name=display_name,
            last_seen_at=datetime.now(UTC),
        )
        self.session.add(robot)
        await self.session.commit()
        await self.session.refresh(robot)
        self.event_bus.publish(
            "robot.discovered",
            robot_id=robot.id,
            payload={
                "manufacturer": robot.manufacturer,
                "serialNumber": robot.serial_number,
            },
        )
        return robot

    async def update_connection_state(self, robot_id: str, state: str) -> Robot:
        robot = await self._get_robot_or_raise(robot_id)
        robot.last_connection_state = state
        await self._touch_and_commit(robot)
        self.event_bus.publish(
            "robot.connection.updated",
            robot_id=robot.id,
            payload={"connectionState": state},
        )
        return robot

    async def update_factsheet(self, robot_id: str, factsheet: dict[str, Any]) -> Robot:
        robot = await self._get_robot_or_raise(robot_id)
        robot.factsheet = factsheet
        robot.capabilities = self._extract_capabilities(factsheet)
        await self._touch_and_commit(robot)
        self.event_bus.publish(
            "robot.factsheet.updated", robot_id=robot.id, payload=factsheet
        )
        return robot

    async def save_state_snapshot(
        self, robot_id: str, payload: dict[str, Any]
    ) -> RobotStateSnapshot:
        robot = await self._get_robot_or_raise(robot_id)
        battery_state = payload.get("batteryState") or {}
        power_supply = payload.get("powerSupply") or {}
        snapshot = RobotStateSnapshot(
            robot_id=robot.id,
            header_id=payload.get("headerId"),
            order_id=payload.get("orderId"),
            order_update_id=payload.get("orderUpdateId"),
            last_node_id=payload.get("lastNodeId"),
            last_node_sequence_id=payload.get("lastNodeSequenceId"),
            battery_charge=power_supply.get("stateOfCharge", battery_state.get("batteryCharge")),
            operating_mode=payload.get("operatingMode"),
            errors=payload.get("errors"),
            safety_state=payload.get("safetyState"),
            agv_position=payload.get("mobileRobotPosition") or payload.get("agvPosition"),
            node_states=payload.get("nodeStates"),
            edge_states=payload.get("edgeStates"),
            action_states=payload.get("actionStates"),
            raw_payload=payload,
        )
        robot.last_seen_at = datetime.now(UTC)
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        await MissionStatusService(self.session, self.event_bus).reconcile(robot.id, payload)
        self.event_bus.publish("robot.state.updated", robot_id=robot.id, payload=payload)
        return snapshot

    async def get_latest_state(self, robot_id: str) -> RobotStateSnapshot | None:
        result = await self.session.execute(
            select(RobotStateSnapshot)
            .where(RobotStateSnapshot.robot_id == robot_id)
            .order_by(RobotStateSnapshot.received_at.desc(), RobotStateSnapshot.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_robot_or_raise(self, robot_id: str) -> Robot:
        robot = await self.session.get(Robot, robot_id)
        if robot is None:
            raise ValueError(f"Robot not found: {robot_id}")
        return robot

    async def _touch_and_commit(self, robot: Robot) -> None:
        robot.last_seen_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(robot)

    def _extract_capabilities(self, factsheet: dict[str, Any]) -> dict[str, Any]:
        return {
            "typeSpecification": factsheet.get("typeSpecification"),
            "protocolLimits": factsheet.get("protocolLimits"),
            "protocolFeatures": factsheet.get("protocolFeatures"),
            "agvGeometry": factsheet.get("agvGeometry"),
            "loadSpecification": factsheet.get("loadSpecification"),
        }
