from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, deferred, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def json_type() -> JSON:
    return JSON().with_variant(JSONB(), "postgresql")


class Robot(Base):
    __tablename__ = "robots"
    __table_args__ = (UniqueConstraint("manufacturer", "serial_number", name="uq_robot_identity"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    manufacturer: Mapped[str] = mapped_column(String(128), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(160))
    protocol_version: Mapped[str] = mapped_column(String(16), default="3.0.0")
    last_connection_state: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    factsheet: Mapped[dict[str, Any] | None] = mapped_column(json_type())
    capabilities: Mapped[dict[str, Any] | None] = mapped_column(json_type())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    state_snapshots: Mapped[list["RobotStateSnapshot"]] = relationship(cascade="all, delete-orphan")


class RobotStateSnapshot(Base):
    __tablename__ = "robot_state_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    robot_id: Mapped[str] = mapped_column(
        ForeignKey("robots.id", ondelete="CASCADE"), nullable=False
    )
    header_id: Mapped[int | None]
    order_id: Mapped[str | None] = mapped_column(String(128))
    order_update_id: Mapped[int | None]
    last_node_id: Mapped[str | None] = mapped_column(String(128))
    last_node_sequence_id: Mapped[int | None]
    battery_charge: Mapped[float | None]
    operating_mode: Mapped[str | None] = mapped_column(String(64))
    errors: Mapped[list[dict[str, Any]] | None] = mapped_column(json_type())
    safety_state: Mapped[dict[str, Any] | None] = mapped_column(json_type())
    agv_position: Mapped[dict[str, Any] | None] = mapped_column(json_type())
    node_states: Mapped[list[dict[str, Any]] | None] = mapped_column(json_type())
    edge_states: Mapped[list[dict[str, Any]] | None] = mapped_column(json_type())
    action_states: Mapped[list[dict[str, Any]] | None] = mapped_column(json_type())
    raw_payload: Mapped[dict[str, Any]] = mapped_column(json_type(), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MapLayout(Base):
    __tablename__ = "maps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    floor: Mapped[str | None] = mapped_column(String(80))
    nodes: Mapped[list["MapNode"]] = relationship(cascade="all, delete-orphan")
    edges: Mapped[list["MapEdge"]] = relationship(cascade="all, delete-orphan")


class MapBackground(Base):
    __tablename__ = "map_backgrounds"

    map_id: Mapped[str] = mapped_column(
        ForeignKey("maps.id", ondelete="CASCADE"), primary_key=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(32), nullable=False)
    image_data: Mapped[bytes] = deferred(mapped_column(LargeBinary, nullable=False))
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    meters_per_pixel: Mapped[float | None] = mapped_column(Float)
    origin_pixel_x: Mapped[float | None] = mapped_column(Float)
    origin_pixel_y: Mapped[float | None] = mapped_column(Float)
    rotation_degrees: Mapped[float | None] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MapNode(Base):
    __tablename__ = "map_nodes"
    __table_args__ = (UniqueConstraint("map_id", "node_key", name="uq_map_node_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    map_id: Mapped[str] = mapped_column(ForeignKey("maps.id", ondelete="CASCADE"), nullable=False)
    node_key: Mapped[str] = mapped_column(String(128), nullable=False)
    x: Mapped[float] = mapped_column(default=0.0)
    y: Mapped[float] = mapped_column(default=0.0)
    theta: Mapped[float] = mapped_column(default=0.0)
    node_type: Mapped[str] = mapped_column(String(32), default="waypoint")


class MapEdge(Base):
    __tablename__ = "map_edges"
    __table_args__ = (UniqueConstraint("map_id", "edge_key", name="uq_map_edge_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    map_id: Mapped[str] = mapped_column(ForeignKey("maps.id", ondelete="CASCADE"), nullable=False)
    edge_key: Mapped[str] = mapped_column(String(128), nullable=False)
    from_node_key: Mapped[str] = mapped_column(String(128), nullable=False)
    to_node_key: Mapped[str] = mapped_column(String(128), nullable=False)
    distance: Mapped[float] = mapped_column(default=1.0)
    bidirectional: Mapped[bool] = mapped_column(default=False)


class MapObstacle(Base):
    __tablename__ = "map_obstacles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    map_id: Mapped[str] = mapped_column(
        ForeignKey("maps.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    points: Mapped[list[dict[str, float]]] = mapped_column(json_type(), nullable=False)
    safety_margin: Mapped[float] = mapped_column(Float, default=0.0)
    active: Mapped[bool] = mapped_column(default=True)


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    map_id: Mapped[str | None] = mapped_column(ForeignKey("maps.id"))
    assigned_robot_id: Mapped[str | None] = mapped_column(ForeignKey("robots.id"))
    start_node_key: Mapped[str] = mapped_column(String(128), nullable=False)
    goal_node_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    priority: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MissionOrder(Base):
    __tablename__ = "mission_orders"
    __table_args__ = (
        UniqueConstraint("robot_id", "header_id", name="uq_mission_order_robot_header"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    mission_id: Mapped[str] = mapped_column(
        ForeignKey("missions.id", ondelete="CASCADE"), nullable=False
    )
    robot_id: Mapped[str] = mapped_column(ForeignKey("robots.id"), nullable=False)
    order_id: Mapped[str] = mapped_column(String(128), nullable=False)
    order_update_id: Mapped[int] = mapped_column(default=0)
    header_id: Mapped[int] = mapped_column(nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(json_type(), nullable=False)
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MqttMessageLog(Base):
    __tablename__ = "mqtt_message_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    qos: Mapped[int] = mapped_column(default=0)
    retain: Mapped[bool] = mapped_column(default=False)
    robot_id: Mapped[str | None] = mapped_column(ForeignKey("robots.id"))
    message_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(json_type(), nullable=False)
    schema_valid: Mapped[bool] = mapped_column(default=False)
    validation_errors: Mapped[list[str]] = mapped_column(json_type(), default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
AsyncSessionMaker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionMaker() as session:
        yield session
