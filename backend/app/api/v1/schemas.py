from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RobotCreate(BaseModel):
    manufacturer: str
    serial_number: str = Field(alias="serialNumber")
    display_name: str | None = Field(default=None, alias="displayName")


class RobotRead(BaseModel):
    id: str
    manufacturer: str
    serial_number: str = Field(serialization_alias="serialNumber")
    display_name: str | None = Field(serialization_alias="displayName")
    protocol_version: str = Field(serialization_alias="protocolVersion")
    last_connection_state: str = Field(serialization_alias="lastConnectionState")


class RobotStateRead(BaseModel):
    id: str
    robot_id: str = Field(serialization_alias="robotId")
    header_id: int | None = Field(serialization_alias="headerId")
    order_id: str | None = Field(serialization_alias="orderId")
    order_update_id: int | None = Field(serialization_alias="orderUpdateId")
    last_node_id: str | None = Field(serialization_alias="lastNodeId")
    last_node_sequence_id: int | None = Field(serialization_alias="lastNodeSequenceId")
    battery_charge: float | None = Field(serialization_alias="batteryCharge")
    operating_mode: str | None = Field(serialization_alias="operatingMode")
    errors: list[dict[str, Any]] | None
    safety_state: dict[str, Any] | None = Field(serialization_alias="safetyState")
    agv_position: dict[str, Any] | None = Field(serialization_alias="agvPosition")
    node_states: list[dict[str, Any]] | None = Field(serialization_alias="nodeStates")
    edge_states: list[dict[str, Any]] | None = Field(serialization_alias="edgeStates")
    action_states: list[dict[str, Any]] | None = Field(serialization_alias="actionStates")
    raw_payload: dict[str, Any] = Field(serialization_alias="rawPayload")
    received_at: datetime = Field(serialization_alias="receivedAt")


class InstantActionCreate(BaseModel):
    action_type: str = Field(alias="actionType", min_length=1)
    action_parameters: list[dict[str, Any]] | None = Field(
        default=None, alias="actionParameters"
    )


class InstantActionRead(BaseModel):
    accepted: bool
    topic: str
    payload: dict[str, Any]
    errors: list[str]


class MapCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None


class MapRead(BaseModel):
    id: str
    name: str
    description: str | None


class MapNodeRead(BaseModel):
    id: str
    node_key: str = Field(serialization_alias="nodeKey")
    x: float
    y: float
    theta: float
    node_type: str = Field(serialization_alias="nodeType")


class MapEdgeRead(BaseModel):
    id: str
    edge_key: str = Field(serialization_alias="edgeKey")
    from_node_key: str = Field(serialization_alias="fromNodeKey")
    to_node_key: str = Field(serialization_alias="toNodeKey")
    distance: float
    bidirectional: bool
    blocked: bool = False
    block_reasons: list[str] = Field(default_factory=list, serialization_alias="blockReasons")


class CalibrationPoint(BaseModel):
    x: float
    y: float


class MapObstacleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    points: list[CalibrationPoint] = Field(min_length=3)
    safety_margin: float = Field(default=0.0, alias="safetyMargin", ge=0)


class MapObstacleRead(BaseModel):
    id: str
    name: str
    points: list[CalibrationPoint]
    safety_margin: float = Field(serialization_alias="safetyMargin")
    active: bool


class MapCalibrationRead(BaseModel):
    meters_per_pixel: float = Field(serialization_alias="metersPerPixel")
    origin_pixel_x: float = Field(serialization_alias="originPixelX")
    origin_pixel_y: float = Field(serialization_alias="originPixelY")
    rotation_degrees: float = Field(serialization_alias="rotationDegrees")


class MapBackgroundRead(BaseModel):
    filename: str
    content_type: str = Field(serialization_alias="contentType")
    width: int
    height: int
    updated_at: datetime = Field(serialization_alias="updatedAt")
    calibration: MapCalibrationRead | None = None


class MapDetailRead(MapRead):
    nodes: list[MapNodeRead]
    edges: list[MapEdgeRead]
    background: MapBackgroundRead | None = None
    obstacles: list[MapObstacleRead] = Field(default_factory=list)


class MapCalibrationUpdate(BaseModel):
    pixel_point_a: CalibrationPoint = Field(alias="pixelPointA")
    pixel_point_b: CalibrationPoint = Field(alias="pixelPointB")
    world_point_a: CalibrationPoint = Field(alias="worldPointA")
    world_point_b: CalibrationPoint = Field(alias="worldPointB")


class NodeCreate(BaseModel):
    node_key: str = Field(alias="nodeKey", min_length=1, max_length=128)
    x: float
    y: float
    theta: float = 0.0


class NodeUpdate(BaseModel):
    x: float
    y: float
    theta: float | None = None


class EdgeCreate(BaseModel):
    edge_key: str = Field(alias="edgeKey", min_length=1, max_length=128)
    from_node_key: str = Field(alias="fromNodeKey", min_length=1, max_length=128)
    to_node_key: str = Field(alias="toNodeKey", min_length=1, max_length=128)
    distance: float = Field(default=1.0, gt=0)
    bidirectional: bool = False


class RoutePreviewRequest(BaseModel):
    start_node_key: str = Field(alias="startNodeKey")
    goal_node_key: str = Field(alias="goalNodeKey")


class RoutePreviewRead(BaseModel):
    node_keys: list[str] = Field(serialization_alias="nodeKeys")


class MissionCreate(BaseModel):
    map_id: str = Field(alias="mapId")
    assigned_robot_id: str | None = Field(default=None, alias="assignedRobotId")
    start_node_key: str = Field(alias="startNodeKey")
    goal_node_key: str = Field(alias="goalNodeKey")
    priority: int = 0


class MissionRead(BaseModel):
    id: str
    map_id: str | None = Field(serialization_alias="mapId")
    assigned_robot_id: str | None = Field(serialization_alias="assignedRobotId")
    start_node_key: str = Field(serialization_alias="startNodeKey")
    goal_node_key: str = Field(serialization_alias="goalNodeKey")
    status: str
    priority: int


class MissionDispatchRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    accepted: bool
    topic: str
    payload: dict[str, Any]
    errors: list[str]


class MqttMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    direction: Literal["inbound", "outbound"]
    topic: str
    qos: int
    retain: bool
    robot_id: str | None = Field(serialization_alias="robotId")
    message_type: str = Field(serialization_alias="messageType")
    payload: dict[str, Any]
    schema_valid: bool = Field(serialization_alias="schemaValid")
    validation_errors: list[str] = Field(serialization_alias="validationErrors")
    created_at: datetime = Field(serialization_alias="createdAt")


class MqttMessagePage(BaseModel):
    items: list[MqttMessageRead]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int
    pages: int
