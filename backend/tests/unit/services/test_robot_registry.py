import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base, Mission
from app.services.robot_registry import RobotRegistryService


@pytest.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db_session:
        yield db_session
    await engine.dispose()


async def test_get_or_create_robot_is_idempotent(session: AsyncSession) -> None:
    service = RobotRegistryService(session)

    first = await service.get_or_create("ResearchBot", "RB001")
    second = await service.get_or_create("ResearchBot", "RB001")

    assert first.id == second.id
    assert second.manufacturer == "ResearchBot"
    assert second.serial_number == "RB001"


async def test_update_connection_state_updates_last_seen(session: AsyncSession) -> None:
    service = RobotRegistryService(session)
    robot = await service.get_or_create("ResearchBot", "RB002")

    updated = await service.update_connection_state(robot.id, "ONLINE")

    assert updated.last_connection_state == "ONLINE"
    assert updated.last_seen_at is not None


async def test_update_factsheet_persists_capabilities_payload(session: AsyncSession) -> None:
    service = RobotRegistryService(session)
    robot = await service.get_or_create("ResearchBot", "RB003")
    factsheet = {
        "headerId": 1,
        "manufacturer": "ResearchBot",
        "serialNumber": "RB003",
        "version": "3.0.0",
        "typeSpecification": {"seriesName": "ResearchBot"},
    }

    updated = await service.update_factsheet(robot.id, factsheet)

    assert updated.factsheet == factsheet
    assert updated.last_seen_at is not None


async def test_save_state_snapshot_and_read_latest_state(session: AsyncSession) -> None:
    service = RobotRegistryService(session)
    robot = await service.get_or_create("ResearchBot", "RB004")
    payload = {
        "headerId": 10,
        "orderId": "order-1",
        "orderUpdateId": 0,
        "lastNodeId": "A",
        "lastNodeSequenceId": 0,
        "batteryState": {"batteryCharge": 87.5},
        "operatingMode": "AUTOMATIC",
        "errors": [],
        "safetyState": {"eStop": "NONE", "fieldViolation": False},
        "mobileRobotPosition": {
            "x": 1.0,
            "y": 2.0,
            "theta": 0.0,
            "mapId": "lab",
            "localized": True,
        },
        "nodeStates": [],
        "edgeStates": [],
        "actionStates": [],
    }

    snapshot = await service.save_state_snapshot(robot.id, payload)
    latest = await service.get_latest_state(robot.id)

    assert snapshot.robot_id == robot.id
    assert latest is not None
    assert latest.id == snapshot.id
    assert latest.battery_charge == 87.5
    assert latest.agv_position == payload["mobileRobotPosition"]
    assert latest.raw_payload == payload


async def test_robot_state_reconciles_mission_progress(session: AsyncSession) -> None:
    service = RobotRegistryService(session)
    robot = await service.get_or_create("ResearchBot", "RB005")
    mission = Mission(
        id="mission-live",
        assigned_robot_id=robot.id,
        start_node_key="A",
        goal_node_key="B",
        status="sent",
        priority=0,
    )
    session.add(mission)
    await session.commit()

    await service.save_state_snapshot(
        robot.id,
        {
            "orderId": mission.id,
            "lastNodeId": "A",
            "nodeStates": [{"nodeId": "B"}],
            "edgeStates": [],
            "actionStates": [],
            "driving": True,
            "errors": [],
        },
    )
    assert mission.status == "running"

    await service.save_state_snapshot(
        robot.id,
        {
            "orderId": mission.id,
            "lastNodeId": "B",
            "nodeStates": [],
            "edgeStates": [],
            "actionStates": [],
            "driving": False,
            "errors": [],
        },
    )
    assert mission.status == "completed"
