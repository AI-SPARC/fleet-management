from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import undefer

from app.api.deps import SessionDep
from app.api.v1.schemas import (
    EdgeCreate,
    MapBackgroundRead,
    MapCalibrationRead,
    MapCalibrationUpdate,
    MapCreate,
    MapDetailRead,
    MapEdgeRead,
    MapNodeRead,
    MapObstacleCreate,
    MapObstacleRead,
    MapRead,
    NodeCreate,
    NodeUpdate,
    RoutePreviewRead,
    RoutePreviewRequest,
)
from app.db.base import MapBackground, MapEdge, MapLayout, MapNode, MapObstacle
from app.services.map_background_service import MapBackgroundService, Point
from app.services.map_obstacle_service import MapObstacleService
from app.services.map_obstacle_service import Point as ObstaclePoint
from app.services.map_service import MapService

router = APIRouter(prefix="/maps", tags=["maps"])


@router.get("", response_model=list[MapRead])
async def list_maps(session: SessionDep) -> list[MapLayout]:
    result = await session.execute(select(MapLayout).order_by(MapLayout.name))
    return list(result.scalars())


@router.post("", response_model=MapRead, status_code=status.HTTP_201_CREATED)
async def create_map(payload: MapCreate, session: SessionDep) -> MapLayout:
    return await MapService(session).create_map(payload.name, payload.description)


@router.get("/{map_id}", response_model=MapDetailRead)
async def get_map(map_id: str, session: SessionDep) -> MapDetailRead:
    layout = await session.get(MapLayout, map_id)
    if layout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Map not found")
    nodes = list(
        (
            await session.execute(
                select(MapNode).where(MapNode.map_id == map_id).order_by(MapNode.node_key)
            )
        ).scalars()
    )
    edges = list(
        (
            await session.execute(
                select(MapEdge).where(MapEdge.map_id == map_id).order_by(MapEdge.edge_key)
            )
        ).scalars()
    )
    background = await session.get(MapBackground, map_id)
    obstacles = list(
        (
            await session.execute(
                select(MapObstacle).where(MapObstacle.map_id == map_id).order_by(MapObstacle.name)
            )
        ).scalars()
    )
    block_reasons = await MapObstacleService(session).block_reasons(nodes, edges, obstacles)
    return MapDetailRead(
        id=layout.id,
        name=layout.name,
        description=layout.description,
        nodes=[MapNodeRead.model_validate(node, from_attributes=True) for node in nodes],
        edges=[
            MapEdgeRead(
                id=edge.id,
                edge_key=edge.edge_key,
                from_node_key=edge.from_node_key,
                to_node_key=edge.to_node_key,
                distance=edge.distance,
                bidirectional=edge.bidirectional,
                blocked=edge.edge_key in block_reasons,
                block_reasons=block_reasons.get(edge.edge_key, []),
            )
            for edge in edges
        ],
        background=_background_read(background) if background is not None else None,
        obstacles=[
            MapObstacleRead.model_validate(obstacle, from_attributes=True)
            for obstacle in obstacles
        ],
    )


@router.put("/{map_id}/background", response_model=MapBackgroundRead)
async def upload_map_background(
    map_id: str,
    request: Request,
    session: SessionDep,
    filename: str = Query(default="map-background", max_length=255),
) -> MapBackgroundRead:
    try:
        background = await MapBackgroundService(session).upload(
            map_id,
            filename,
            request.headers.get("content-type"),
            await request.body(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=_map_error_status(exc), detail=str(exc)) from exc
    return _background_read(background)


@router.get("/{map_id}/background/content")
async def get_map_background_content(map_id: str, session: SessionDep) -> Response:
    background = (
        await session.execute(
            select(MapBackground)
            .options(undefer(MapBackground.image_data))
            .where(MapBackground.map_id == map_id)
        )
    ).scalar_one_or_none()
    if background is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Map background not found"
        )
    return Response(
        content=background.image_data,
        media_type=background.content_type,
        headers={
            "Cache-Control": "no-cache",
            "Content-Disposition": f'inline; filename="{background.filename}"',
        },
    )


@router.put("/{map_id}/background/calibration", response_model=MapBackgroundRead)
async def calibrate_map_background(
    map_id: str,
    payload: MapCalibrationUpdate,
    session: SessionDep,
) -> MapBackgroundRead:
    try:
        background = await MapBackgroundService(session).calibrate(
            map_id,
            Point(payload.pixel_point_a.x, payload.pixel_point_a.y),
            Point(payload.pixel_point_b.x, payload.pixel_point_b.y),
            Point(payload.world_point_a.x, payload.world_point_a.y),
            Point(payload.world_point_b.x, payload.world_point_b.y),
        )
    except ValueError as exc:
        raise HTTPException(status_code=_map_error_status(exc), detail=str(exc)) from exc
    return _background_read(background)


@router.delete("/{map_id}/background", status_code=status.HTTP_204_NO_CONTENT)
async def delete_map_background(map_id: str, session: SessionDep) -> Response:
    try:
        await MapBackgroundService(session).delete(map_id)
    except ValueError as exc:
        raise HTTPException(status_code=_map_error_status(exc), detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{map_id}/obstacles",
    response_model=MapObstacleRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_map_obstacle(
    map_id: str, payload: MapObstacleCreate, session: SessionDep
) -> MapObstacleRead:
    try:
        obstacle = await MapObstacleService(session).create(
            map_id,
            payload.name,
            [ObstaclePoint(point.x, point.y) for point in payload.points],
            payload.safety_margin,
        )
    except ValueError as exc:
        raise HTTPException(status_code=_map_error_status(exc), detail=str(exc)) from exc
    return MapObstacleRead.model_validate(obstacle, from_attributes=True)


@router.delete(
    "/{map_id}/obstacles/{obstacle_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_map_obstacle(
    map_id: str, obstacle_id: str, session: SessionDep
) -> Response:
    try:
        await MapObstacleService(session).delete(map_id, obstacle_id)
    except ValueError as exc:
        raise HTTPException(status_code=_map_error_status(exc), detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{map_id}/nodes", status_code=status.HTTP_201_CREATED)
async def add_node(map_id: str, payload: NodeCreate, session: SessionDep) -> dict[str, str]:
    try:
        node = await MapService(session).add_node(
            map_id, payload.node_key, payload.x, payload.y, payload.theta
        )
    except ValueError as exc:
        raise HTTPException(status_code=_map_error_status(exc), detail=str(exc)) from exc
    return {"id": node.id, "nodeKey": node.node_key}


@router.patch("/{map_id}/nodes/{node_key}", response_model=MapNodeRead)
async def update_node(
    map_id: str,
    node_key: str,
    payload: NodeUpdate,
    session: SessionDep,
) -> MapNodeRead:
    try:
        node = await MapService(session).update_node(
            map_id, node_key, payload.x, payload.y, payload.theta
        )
    except ValueError as exc:
        raise HTTPException(status_code=_map_error_status(exc), detail=str(exc)) from exc
    return MapNodeRead.model_validate(node, from_attributes=True)


@router.post("/{map_id}/edges", status_code=status.HTTP_201_CREATED)
async def add_edge(map_id: str, payload: EdgeCreate, session: SessionDep) -> dict[str, str]:
    try:
        edge = await MapService(session).add_edge(
            map_id,
            payload.edge_key,
            payload.from_node_key,
            payload.to_node_key,
            payload.distance,
            payload.bidirectional,
        )
    except ValueError as exc:
        raise HTTPException(status_code=_map_error_status(exc), detail=str(exc)) from exc
    return {"id": edge.id, "edgeKey": edge.edge_key}


@router.post("/{map_id}/route-preview", response_model=RoutePreviewRead)
async def route_preview(
    map_id: str, payload: RoutePreviewRequest, session: SessionDep
) -> RoutePreviewRead:
    try:
        node_keys = await MapService(session).route_preview(
            map_id, payload.start_node_key, payload.goal_node_key
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RoutePreviewRead(node_keys=node_keys)


def _map_error_status(exc: ValueError) -> int:
    if str(exc) in {
        "Map not found",
        "Map background not found",
        "Map node not found",
        "Map obstacle not found",
    }:
        return status.HTTP_404_NOT_FOUND
    return status.HTTP_422_UNPROCESSABLE_CONTENT


def _background_read(background: MapBackground) -> MapBackgroundRead:
    calibration = None
    meters_per_pixel = background.meters_per_pixel
    origin_pixel_x = background.origin_pixel_x
    origin_pixel_y = background.origin_pixel_y
    rotation_degrees = background.rotation_degrees
    if (
        meters_per_pixel is not None
        and origin_pixel_x is not None
        and origin_pixel_y is not None
        and rotation_degrees is not None
    ):
        calibration = MapCalibrationRead(
            meters_per_pixel=meters_per_pixel,
            origin_pixel_x=origin_pixel_x,
            origin_pixel_y=origin_pixel_y,
            rotation_degrees=rotation_degrees,
        )
    return MapBackgroundRead(
        filename=background.filename,
        content_type=background.content_type,
        width=background.width,
        height=background.height,
        updated_at=background.updated_at,
        calibration=calibration,
    )
