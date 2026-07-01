from dataclasses import dataclass

import networkx as nx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import MapEdge, MapLayout, MapNode


@dataclass(frozen=True)
class RouteLeg:
    edge_key: str
    from_node_key: str
    to_node_key: str


@dataclass(frozen=True)
class PlannedRoute:
    map_id: str
    nodes: list[MapNode]
    legs: list[RouteLeg]


class MapService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_map(self, name: str, description: str | None = None) -> MapLayout:
        layout = MapLayout(name=name, description=description)
        self.session.add(layout)
        await self.session.commit()
        await self.session.refresh(layout)
        return layout

    async def add_node(
        self, map_id: str, node_key: str, x: float, y: float, theta: float = 0.0
    ) -> MapNode:
        await self._ensure_map_exists(map_id)
        existing = await self.session.scalar(
            select(MapNode.id).where(MapNode.map_id == map_id, MapNode.node_key == node_key)
        )
        if existing is not None:
            raise ValueError(f"Node key already exists: {node_key}")
        node = MapNode(map_id=map_id, node_key=node_key, x=x, y=y, theta=theta)
        self.session.add(node)
        await self.session.commit()
        await self.session.refresh(node)
        return node

    async def add_edge(
        self,
        map_id: str,
        edge_key: str,
        from_node_key: str,
        to_node_key: str,
        distance: float,
        bidirectional: bool = False,
    ) -> MapEdge:
        await self._ensure_map_exists(map_id)
        if distance <= 0:
            raise ValueError("Edge distance must be positive")
        existing = await self.session.scalar(
            select(MapEdge.id).where(MapEdge.map_id == map_id, MapEdge.edge_key == edge_key)
        )
        if existing is not None:
            raise ValueError(f"Edge key already exists: {edge_key}")
        node_keys = set(
            (
                await self.session.execute(
                    select(MapNode.node_key).where(
                        MapNode.map_id == map_id,
                        MapNode.node_key.in_([from_node_key, to_node_key]),
                    )
                )
            ).scalars()
        )
        missing = {from_node_key, to_node_key} - node_keys
        if missing:
            raise ValueError(f"Map nodes not found: {', '.join(sorted(missing))}")
        edge = MapEdge(
            map_id=map_id,
            edge_key=edge_key,
            from_node_key=from_node_key,
            to_node_key=to_node_key,
            distance=distance,
            bidirectional=bidirectional,
        )
        self.session.add(edge)
        await self.session.commit()
        await self.session.refresh(edge)
        return edge

    async def update_node(
        self,
        map_id: str,
        node_key: str,
        x: float,
        y: float,
        theta: float | None = None,
    ) -> MapNode:
        await self._ensure_map_exists(map_id)
        node = await self.session.scalar(
            select(MapNode).where(MapNode.map_id == map_id, MapNode.node_key == node_key)
        )
        if node is None:
            raise ValueError("Map node not found")
        node.x = x
        node.y = y
        if theta is not None:
            node.theta = theta
        await self.session.commit()
        await self.session.refresh(node)
        return node

    async def route_preview(
        self,
        map_id: str,
        start_node_key: str,
        goal_node_key: str,
    ) -> list[str]:
        route = await self.plan_route(map_id, start_node_key, goal_node_key)
        return [node.node_key for node in route.nodes]

    async def plan_route(
        self,
        map_id: str,
        start_node_key: str,
        goal_node_key: str,
    ) -> PlannedRoute:
        layout = await self.session.get(MapLayout, map_id)
        if layout is None:
            raise ValueError("Map not found")

        nodes = list(
            (
                await self.session.execute(select(MapNode).where(MapNode.map_id == map_id))
            ).scalars()
        )
        edges = list(
            (
                await self.session.execute(select(MapEdge).where(MapEdge.map_id == map_id))
            ).scalars()
        )
        nodes_by_key = {node.node_key: node for node in nodes}
        graph: nx.DiGraph[str] = nx.DiGraph()
        graph.add_nodes_from(nodes_by_key)
        for edge in edges:
            graph.add_edge(
                edge.from_node_key,
                edge.to_node_key,
                weight=edge.distance,
                edge_key=edge.edge_key,
            )
            if edge.bidirectional:
                graph.add_edge(
                    edge.to_node_key,
                    edge.from_node_key,
                    weight=edge.distance,
                    edge_key=edge.edge_key,
                )
        try:
            node_keys = list(
                nx.shortest_path(graph, start_node_key, goal_node_key, weight="weight")
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
            raise ValueError("No route found") from exc

        legs = [
            RouteLeg(
                edge_key=graph[from_key][to_key]["edge_key"],
                from_node_key=from_key,
                to_node_key=to_key,
            )
            for from_key, to_key in zip(node_keys, node_keys[1:], strict=False)
        ]
        return PlannedRoute(
            map_id=map_id,
            nodes=[nodes_by_key[node_key] for node_key in node_keys],
            legs=legs,
        )

    async def _ensure_map_exists(self, map_id: str) -> None:
        if await self.session.get(MapLayout, map_id) is None:
            raise ValueError("Map not found")
