from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_session
from app.db.base import Base, RobotStateSnapshot
from app.main import app
from app.mqtt.outbound import RecordingMqttPublisher, get_mqtt_publisher
from app.services.robot_registry import RobotRegistryService


@dataclass(frozen=True)
class ApiTestContext:
    client: AsyncClient
    maker: async_sessionmaker[AsyncSession]
    publisher: RecordingMqttPublisher


@pytest.fixture
async def context() -> AsyncIterator[ApiTestContext]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    publisher = RecordingMqttPublisher()

    async def override_session():
        async with maker() as session:
            yield session

    def override_publisher() -> RecordingMqttPublisher:
        return publisher

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_mqtt_publisher] = override_publisher
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield ApiTestContext(client=test_client, maker=maker, publisher=publisher)
    app.dependency_overrides.clear()
    await engine.dispose()


async def test_create_and_list_robots(context: ApiTestContext) -> None:
    create_response = await context.client.post(
        "/api/v1/robots",
        json={"manufacturer": "ResearchBot", "serialNumber": "RB001", "displayName": "Lab robot"},
    )

    assert create_response.status_code == 201
    assert create_response.json()["serialNumber"] == "RB001"

    list_response = await context.client.get("/api/v1/robots")

    assert list_response.status_code == 200
    assert list_response.json()[0]["manufacturer"] == "ResearchBot"


async def test_get_robot_detail_latest_state_and_factsheet(context: ApiTestContext) -> None:
    create_response = await context.client.post(
        "/api/v1/robots",
        json={"manufacturer": "ResearchBot", "serialNumber": "RB010", "displayName": "Robot 10"},
    )
    robot_id = create_response.json()["id"]

    async with context.maker() as session:
        service = RobotRegistryService(session)
        await service.update_factsheet(robot_id, {"typeSpecification": {"seriesName": "RB"}})
        await service.save_state_snapshot(
            robot_id,
            {
                "headerId": 99,
                "orderId": "order-99",
                "orderUpdateId": 1,
                "lastNodeId": "B",
                "lastNodeSequenceId": 2,
                "batteryState": {"batteryCharge": 42.0},
                "operatingMode": "AUTOMATIC",
                "errors": [],
                "safetyState": {"eStop": "NONE", "fieldViolation": False},
                "agvPosition": {"x": 1.0, "y": 2.0, "theta": 0.0, "mapId": "lab"},
                "nodeStates": [],
                "edgeStates": [],
                "actionStates": [],
            },
        )

    detail_response = await context.client.get(f"/api/v1/robots/{robot_id}")
    state_response = await context.client.get(f"/api/v1/robots/{robot_id}/state/latest")
    factsheet_response = await context.client.get(f"/api/v1/robots/{robot_id}/factsheet")

    assert detail_response.status_code == 200
    assert detail_response.json()["displayName"] == "Robot 10"
    assert state_response.status_code == 200
    assert state_response.json()["batteryCharge"] == 42.0
    assert state_response.json()["rawPayload"]["lastNodeId"] == "B"
    assert factsheet_response.status_code == 200
    assert factsheet_response.json()["typeSpecification"]["seriesName"] == "RB"


async def test_send_cancel_order_instant_action(context: ApiTestContext) -> None:
    robot_response = await context.client.post(
        "/api/v1/robots", json={"manufacturer": "ResearchBot", "serialNumber": "RB-CANCEL"}
    )

    response = await context.client.post(
        f"/api/v1/robots/{robot_response.json()['id']}/instant-actions",
        json={"actionType": "cancelOrder"},
    )

    assert response.status_code == 202
    assert response.json()["payload"]["actions"][0]["actionType"] == "cancelOrder"
    assert context.publisher.publications[-1].topic.endswith("/instantActions")


async def test_create_map_with_nodes_and_route_preview(context: ApiTestContext) -> None:
    map_response = await context.client.post("/api/v1/maps", json={"name": "Lab"})
    map_id = map_response.json()["id"]

    await context.client.post(f"/api/v1/maps/{map_id}/nodes", json={"nodeKey": "A", "x": 0, "y": 0})
    await context.client.post(f"/api/v1/maps/{map_id}/nodes", json={"nodeKey": "B", "x": 1, "y": 0})
    edge_response = await context.client.post(
        f"/api/v1/maps/{map_id}/edges",
        json={"edgeKey": "A-B", "fromNodeKey": "A", "toNodeKey": "B", "distance": 1.0},
    )

    assert edge_response.status_code == 201

    route_response = await context.client.post(
        f"/api/v1/maps/{map_id}/route-preview", json={"startNodeKey": "A", "goalNodeKey": "B"}
    )

    assert route_response.status_code == 200
    assert route_response.json()["nodeKeys"] == ["A", "B"]

    detail_response = await context.client.get(f"/api/v1/maps/{map_id}")
    assert detail_response.status_code == 200
    assert [node["nodeKey"] for node in detail_response.json()["nodes"]] == ["A", "B"]
    assert detail_response.json()["edges"][0] == {
        "id": edge_response.json()["id"],
        "edgeKey": "A-B",
        "fromNodeKey": "A",
        "toNodeKey": "B",
        "distance": 1.0,
        "bidirectional": False,
        "blocked": False,
        "blockReasons": [],
    }


async def test_upload_calibrate_and_read_map_background(context: ApiTestContext) -> None:
    map_response = await context.client.post("/api/v1/maps", json={"name": "Calibrated lab"})
    map_id = map_response.json()["id"]
    image_buffer = BytesIO()
    Image.new("RGB", (800, 400), "white").save(image_buffer, format="PNG")

    upload = await context.client.put(
        f"/api/v1/maps/{map_id}/background",
        params={"filename": "lab.png"},
        content=image_buffer.getvalue(),
        headers={"Content-Type": "image/png"},
    )
    calibration = await context.client.put(
        f"/api/v1/maps/{map_id}/background/calibration",
        json={
            "pixelPointA": {"x": 100, "y": 300},
            "pixelPointB": {"x": 600, "y": 300},
            "worldPointA": {"x": 0, "y": 0},
            "worldPointB": {"x": 10, "y": 0},
        },
    )
    detail = await context.client.get(f"/api/v1/maps/{map_id}")
    content = await context.client.get(f"/api/v1/maps/{map_id}/background/content")

    assert upload.status_code == 200
    assert upload.json() == {
        "filename": "lab.png",
        "contentType": "image/png",
        "width": 800,
        "height": 400,
        "updatedAt": upload.json()["updatedAt"],
        "calibration": None,
    }
    assert calibration.status_code == 200
    assert calibration.json()["calibration"] == {
        "metersPerPixel": 0.02,
        "originPixelX": 100.0,
        "originPixelY": 300.0,
        "rotationDegrees": 0.0,
    }
    assert detail.json()["background"] == calibration.json()
    assert content.status_code == 200
    assert content.headers["content-type"] == "image/png"
    assert content.content == image_buffer.getvalue()


async def test_map_background_rejects_invalid_image(context: ApiTestContext) -> None:
    map_response = await context.client.post("/api/v1/maps", json={"name": "Invalid image"})
    response = await context.client.put(
        f"/api/v1/maps/{map_response.json()['id']}/background",
        content=b"not-an-image",
        headers={"Content-Type": "image/png"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Background must be a valid PNG or JPEG image"


async def test_map_api_rejects_dangling_and_invalid_edges(context: ApiTestContext) -> None:
    map_response = await context.client.post("/api/v1/maps", json={"name": "Validated map"})
    map_id = map_response.json()["id"]
    await context.client.post(
        f"/api/v1/maps/{map_id}/nodes", json={"nodeKey": "A", "x": 0, "y": 0}
    )

    dangling = await context.client.post(
        f"/api/v1/maps/{map_id}/edges",
        json={"edgeKey": "A-B", "fromNodeKey": "A", "toNodeKey": "B", "distance": 1},
    )
    invalid_distance = await context.client.post(
        f"/api/v1/maps/{map_id}/edges",
        json={"edgeKey": "A-A", "fromNodeKey": "A", "toNodeKey": "A", "distance": 0},
    )

    assert dangling.status_code == 422
    assert dangling.json()["detail"] == "Map nodes not found: B"
    assert invalid_distance.status_code == 422


async def test_update_map_node_position(context: ApiTestContext) -> None:
    map_response = await context.client.post("/api/v1/maps", json={"name": "Editable map"})
    map_id = map_response.json()["id"]
    await context.client.post(
        f"/api/v1/maps/{map_id}/nodes",
        json={"nodeKey": "A", "x": 0, "y": 0, "theta": 0.5},
    )

    response = await context.client.patch(
        f"/api/v1/maps/{map_id}/nodes/A", json={"x": 2.5, "y": 3.5}
    )

    assert response.status_code == 200
    assert response.json()["x"] == 2.5
    assert response.json()["y"] == 3.5
    assert response.json()["theta"] == 0.5


async def test_obstacle_blocks_intersecting_route(context: ApiTestContext) -> None:
    map_response = await context.client.post("/api/v1/maps", json={"name": "Obstacle map"})
    map_id = map_response.json()["id"]
    for node_key, x in (("A", 0), ("B", 10)):
        await context.client.post(
            f"/api/v1/maps/{map_id}/nodes",
            json={"nodeKey": node_key, "x": x, "y": 0},
        )
    await context.client.post(
        f"/api/v1/maps/{map_id}/edges",
        json={"edgeKey": "A-B", "fromNodeKey": "A", "toNodeKey": "B", "distance": 10},
    )

    obstacle = await context.client.post(
        f"/api/v1/maps/{map_id}/obstacles",
        json={
            "name": "Pallet",
            "points": [
                {"x": 4, "y": -1},
                {"x": 6, "y": -1},
                {"x": 6, "y": 1},
                {"x": 4, "y": 1},
            ],
            "safetyMargin": 0.1,
        },
    )
    detail = await context.client.get(f"/api/v1/maps/{map_id}")
    blocked_route = await context.client.post(
        f"/api/v1/maps/{map_id}/route-preview",
        json={"startNodeKey": "A", "goalNodeKey": "B"},
    )

    assert obstacle.status_code == 201
    assert detail.json()["edges"][0]["blocked"] is True
    assert detail.json()["edges"][0]["blockReasons"] == ["Pallet"]
    assert blocked_route.status_code == 404

    deleted = await context.client.delete(
        f"/api/v1/maps/{map_id}/obstacles/{obstacle.json()['id']}"
    )
    available_route = await context.client.post(
        f"/api/v1/maps/{map_id}/route-preview",
        json={"startNodeKey": "A", "goalNodeKey": "B"},
    )
    assert deleted.status_code == 204
    assert available_route.status_code == 200


async def test_create_mission(context: ApiTestContext) -> None:
    robot_response = await context.client.post(
        "/api/v1/robots", json={"manufacturer": "ResearchBot", "serialNumber": "RB003"}
    )
    map_response = await context.client.post("/api/v1/maps", json={"name": "Mission map"})
    map_id = map_response.json()["id"]
    await context.client.post(
        f"/api/v1/maps/{map_id}/nodes", json={"nodeKey": "A", "x": 0, "y": 0}
    )
    await context.client.post(
        f"/api/v1/maps/{map_id}/nodes", json={"nodeKey": "B", "x": 1, "y": 0}
    )

    mission_response = await context.client.post(
        "/api/v1/missions",
        json={
            "mapId": map_id,
            "assignedRobotId": robot_response.json()["id"],
            "startNodeKey": "A",
            "goalNodeKey": "B",
        },
    )

    assert mission_response.status_code == 201
    assert mission_response.json()["status"] == "assigned"
    detail_response = await context.client.get(
        f"/api/v1/missions/{mission_response.json()['id']}"
    )
    assert detail_response.status_code == 200
    assert detail_response.json() == mission_response.json()

    async with context.maker() as session:
        session.add_all(
            [
                RobotStateSnapshot(
                    robot_id=robot_response.json()["id"],
                    order_id=mission_response.json()["id"],
                    last_node_id=node_id,
                    battery_charge=charge,
                    agv_position={"x": x, "y": 0, "theta": 0, "mapId": map_id},
                    raw_payload={},
                    received_at=datetime(2026, 7, 2, 12, minute, tzinfo=UTC),
                )
                for minute, node_id, x, charge in ((0, "A", 0, 80), (1, "B", 1, 79))
            ]
        )
        await session.commit()

    trajectory = await context.client.get(
        f"/api/v1/missions/{mission_response.json()['id']}/trajectory"
    )
    assert trajectory.status_code == 200
    assert [point["lastNodeId"] for point in trajectory.json()] == ["A", "B"]
    assert trajectory.json()[1]["x"] == 1.0
    assert mission_response.json()["mapId"] == map_id


async def test_dispatch_mission_publishes_order(context: ApiTestContext) -> None:
    robot_response = await context.client.post(
        "/api/v1/robots", json={"manufacturer": "ResearchBot", "serialNumber": "RB004"}
    )
    map_response = await context.client.post("/api/v1/maps", json={"name": "Dispatch map"})
    map_id = map_response.json()["id"]
    await context.client.post(
        f"/api/v1/maps/{map_id}/nodes", json={"nodeKey": "Dock", "x": 2, "y": 3}
    )
    await context.client.post(
        f"/api/v1/maps/{map_id}/nodes", json={"nodeKey": "Shelf", "x": 8, "y": 5}
    )
    await context.client.post(
        f"/api/v1/maps/{map_id}/edges",
        json={
            "edgeKey": "Dock-Shelf",
            "fromNodeKey": "Dock",
            "toNodeKey": "Shelf",
            "distance": 6.3,
        },
    )
    mission_response = await context.client.post(
        "/api/v1/missions",
        json={
            "mapId": map_id,
            "assignedRobotId": robot_response.json()["id"],
            "startNodeKey": "Dock",
            "goalNodeKey": "Shelf",
        },
    )

    dispatch_response = await context.client.post(
        f"/api/v1/missions/{mission_response.json()['id']}/dispatch"
    )

    assert dispatch_response.status_code == 202
    body = dispatch_response.json()
    assert body["accepted"] is True
    assert body["topic"] == "vda5050/v3/ResearchBot/RB004/order"
    assert body["payload"]["orderId"] == mission_response.json()["id"]
    assert body["payload"]["nodes"][0]["nodePosition"]["x"] == 2
    assert body["payload"]["nodes"][1]["nodePosition"]["x"] == 8
    assert len(context.publisher.publications) == 1
    assert context.publisher.publications[0].topic == "vda5050/v3/ResearchBot/RB004/order"
