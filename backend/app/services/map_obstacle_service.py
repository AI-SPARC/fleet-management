from dataclasses import dataclass
from math import hypot

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.base import MapEdge, MapLayout, MapNode, MapObstacle


@dataclass(frozen=True)
class Point:
    x: float
    y: float


class MapObstacleService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

    async def create(
        self, map_id: str, name: str, points: list[Point], safety_margin: float
    ) -> MapObstacle:
        if await self.session.get(MapLayout, map_id) is None:
            raise ValueError("Map not found")
        validate_polygon(points)
        obstacle = MapObstacle(
            map_id=map_id,
            name=name,
            points=[{"x": point.x, "y": point.y} for point in points],
            safety_margin=safety_margin,
        )
        self.session.add(obstacle)
        await self.session.commit()
        await self.session.refresh(obstacle)
        return obstacle

    async def delete(self, map_id: str, obstacle_id: str) -> None:
        obstacle = await self.session.scalar(
            select(MapObstacle).where(
                MapObstacle.map_id == map_id, MapObstacle.id == obstacle_id
            )
        )
        if obstacle is None:
            raise ValueError("Map obstacle not found")
        await self.session.delete(obstacle)
        await self.session.commit()

    async def block_reasons(
        self,
        nodes: list[MapNode],
        edges: list[MapEdge],
        obstacles: list[MapObstacle],
    ) -> dict[str, list[str]]:
        return edge_block_reasons(
            nodes, edges, obstacles, self.settings.map_default_robot_radius_m
        )


def edge_block_reasons(
    nodes: list[MapNode],
    edges: list[MapEdge],
    obstacles: list[MapObstacle],
    robot_radius: float,
) -> dict[str, list[str]]:
    nodes_by_key = {node.node_key: Point(node.x, node.y) for node in nodes}
    reasons: dict[str, list[str]] = {}
    for edge in edges:
        start = nodes_by_key.get(edge.from_node_key)
        end = nodes_by_key.get(edge.to_node_key)
        if start is None or end is None:
            continue
        for obstacle in obstacles:
            if not obstacle.active:
                continue
            polygon = [Point(point["x"], point["y"]) for point in obstacle.points]
            clearance = robot_radius + obstacle.safety_margin
            if segment_intersects_polygon_corridor(start, end, polygon, clearance):
                reasons.setdefault(edge.edge_key, []).append(obstacle.name)
    return reasons


def validate_polygon(points: list[Point]) -> None:
    if len(points) < 3:
        raise ValueError("Obstacle polygon requires at least three points")
    area = abs(
        sum(
            first.x * second.y - second.x * first.y
            for first, second in _polygon_segments(points)
        )
        / 2
    )
    if area < 1e-6:
        raise ValueError("Obstacle polygon must enclose an area")


def segment_intersects_polygon_corridor(
    start: Point, end: Point, polygon: list[Point], clearance: float
) -> bool:
    if point_in_polygon(start, polygon) or point_in_polygon(end, polygon):
        return True
    return any(
        segment_distance(start, end, polygon_start, polygon_end) <= clearance
        for polygon_start, polygon_end in _polygon_segments(polygon)
    )


def point_in_polygon(point: Point, polygon: list[Point]) -> bool:
    inside = False
    previous = polygon[-1]
    for current in polygon:
        crosses = (current.y > point.y) != (previous.y > point.y)
        if crosses:
            intersection_x = (previous.x - current.x) * (point.y - current.y) / (
                previous.y - current.y
            ) + current.x
            if point.x < intersection_x:
                inside = not inside
        previous = current
    return inside


def segment_distance(a: Point, b: Point, c: Point, d: Point) -> float:
    if segments_intersect(a, b, c, d):
        return 0.0
    return min(
        point_segment_distance(a, c, d),
        point_segment_distance(b, c, d),
        point_segment_distance(c, a, b),
        point_segment_distance(d, a, b),
    )


def segments_intersect(a: Point, b: Point, c: Point, d: Point) -> bool:
    def orientation(first: Point, second: Point, third: Point) -> float:
        return (second.x - first.x) * (third.y - first.y) - (
            second.y - first.y
        ) * (third.x - first.x)

    first = orientation(a, b, c)
    second = orientation(a, b, d)
    third = orientation(c, d, a)
    fourth = orientation(c, d, b)
    epsilon = 1e-9
    if ((first > epsilon and second < -epsilon) or (first < -epsilon and second > epsilon)) and (
        (third > epsilon and fourth < -epsilon) or (third < -epsilon and fourth > epsilon)
    ):
        return True

    def on_segment(first_point: Point, middle: Point, last: Point) -> bool:
        return (
            min(first_point.x, last.x) - epsilon
            <= middle.x
            <= max(first_point.x, last.x) + epsilon
            and min(first_point.y, last.y) - epsilon
            <= middle.y
            <= max(first_point.y, last.y) + epsilon
        )

    return (
        (abs(first) <= epsilon and on_segment(a, c, b))
        or (abs(second) <= epsilon and on_segment(a, d, b))
        or (abs(third) <= epsilon and on_segment(c, a, d))
        or (abs(fourth) <= epsilon and on_segment(c, b, d))
    )


def point_segment_distance(point: Point, start: Point, end: Point) -> float:
    dx = end.x - start.x
    dy = end.y - start.y
    length_squared = dx * dx + dy * dy
    if length_squared == 0:
        return hypot(point.x - start.x, point.y - start.y)
    ratio = max(
        0.0,
        min(1.0, ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_squared),
    )
    projection = Point(start.x + ratio * dx, start.y + ratio * dy)
    return hypot(point.x - projection.x, point.y - projection.y)


def _polygon_segments(points: list[Point]) -> list[tuple[Point, Point]]:
    return list(zip(points, points[1:] + points[:1], strict=True))
