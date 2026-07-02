from dataclasses import dataclass
from typing import Any

from tars_robot_simulator.payloads import (
    RobotIdentity,
    build_connection_payload,
    build_factsheet_payload,
    build_state_payload,
)
from tars_robot_simulator.topics import build_topic


@dataclass(frozen=True)
class Publication:
    topic: str
    payload: dict[str, Any]
    qos: int = 0
    retain: bool = False


class SimulatedRobot:
    def __init__(self, identity: RobotIdentity, *, initial_state_of_charge: float = 80.0) -> None:
        self.identity = identity
        self.header_id = 0
        self.state_of_charge = initial_state_of_charge
        self.current_order_id = ""
        self.current_order_update_id = 0
        self.current_nodes: list[dict[str, Any]] = []
        self.current_edges: list[dict[str, Any]] = []
        self.current_node_index = 0
        self.instant_action_states: list[dict[str, Any]] = []

    def startup_publications(self) -> list[Publication]:
        return [
            self.connection_publication("ONLINE"),
            self.factsheet_publication(),
            self.state_publication(),
        ]

    def connection_publication(self, connection_state: str = "ONLINE") -> Publication:
        return Publication(
            topic=build_topic(self.identity, "connection"),
            payload=build_connection_payload(
                self.identity,
                header_id=self._next_header_id(),
                connection_state=connection_state,  # type: ignore[arg-type]
            ),
            qos=1,
            retain=True,
        )

    def factsheet_publication(self) -> Publication:
        return Publication(
            topic=build_topic(self.identity, "factsheet"),
            payload=build_factsheet_payload(self.identity, header_id=self._next_header_id()),
        )

    def state_publication(self) -> Publication:
        node = self.current_nodes[self.current_node_index] if self.current_nodes else None
        driving = bool(node and self.current_node_index < len(self.current_nodes) - 1)
        remaining_nodes = self.current_nodes[self.current_node_index + 1 :]
        last_sequence_id = int(node.get("sequenceId", 0)) if node else 0
        position = dict(node.get("nodePosition") or {}) if node else None
        if position:
            position["localized"] = True
        publication = Publication(
            topic=build_topic(self.identity, "state"),
            payload=build_state_payload(
                self.identity,
                header_id=self._next_header_id(),
                state_of_charge=self.state_of_charge,
                order_id=self.current_order_id,
                order_update_id=self.current_order_update_id,
                last_node_id=str(node.get("nodeId", "")) if node else "",
                last_node_sequence_id=last_sequence_id,
                driving=driving,
                node_states=[
                    {
                        "nodeId": item["nodeId"],
                        "sequenceId": item["sequenceId"],
                        "released": item.get("released", True),
                    }
                    for item in remaining_nodes
                ],
                edge_states=[
                    {
                        "edgeId": edge["edgeId"],
                        "sequenceId": edge["sequenceId"],
                        "released": edge.get("released", True),
                    }
                    for edge in self.current_edges
                    if int(edge.get("sequenceId", 0)) > last_sequence_id
                ],
                mobile_robot_position=position,
                instant_action_states=self.instant_action_states,
            ),
        )
        if driving:
            self.current_node_index += 1
        return publication

    def apply_order(self, payload: dict[str, Any]) -> None:
        self.current_order_id = str(payload.get("orderId", ""))
        self.current_order_update_id = int(payload.get("orderUpdateId", 0))
        self.current_nodes = list(payload.get("nodes") or [])
        self.current_edges = list(payload.get("edges") or [])
        self.current_node_index = 0
        self.instant_action_states = []

    def apply_instant_actions(self, payload: dict[str, Any]) -> None:
        actions = payload.get("actions") or []
        cancel_actions = [action for action in actions if action.get("actionType") == "cancelOrder"]
        if cancel_actions:
            self.instant_action_states = [
                {"actionId": action["actionId"], "actionStatus": "FINISHED"}
                for action in cancel_actions
            ]
            self.current_order_id = ""
            self.current_order_update_id = 0
            self.current_nodes = []
            self.current_edges = []
            self.current_node_index = 0

    def _next_header_id(self) -> int:
        self.header_id += 1
        return self.header_id
