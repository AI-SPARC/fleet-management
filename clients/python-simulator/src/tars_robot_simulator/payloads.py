from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

ConnectionState = Literal["ONLINE", "OFFLINE", "HIBERNATING", "CONNECTION_BROKEN"]


@dataclass(frozen=True)
class RobotIdentity:
    manufacturer: str = "ResearchBot"
    serial_number: str = "RB-SIM-001"


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def build_connection_payload(
    identity: RobotIdentity,
    *,
    header_id: int,
    connection_state: ConnectionState = "ONLINE",
) -> dict:
    return {
        "headerId": header_id,
        "timestamp": utc_timestamp(),
        "version": "3.0.0",
        "manufacturer": identity.manufacturer,
        "serialNumber": identity.serial_number,
        "connectionState": connection_state,
    }


def build_state_payload(
    identity: RobotIdentity,
    *,
    header_id: int,
    state_of_charge: float = 80.0,
    order_id: str = "",
    order_update_id: int = 0,
    last_node_id: str = "",
    last_node_sequence_id: int = 0,
    driving: bool = False,
    node_states: list[dict] | None = None,
    edge_states: list[dict] | None = None,
    mobile_robot_position: dict | None = None,
    instant_action_states: list[dict] | None = None,
) -> dict:
    payload = {
        "headerId": header_id,
        "timestamp": utc_timestamp(),
        "version": "3.0.0",
        "manufacturer": identity.manufacturer,
        "serialNumber": identity.serial_number,
        "orderId": order_id,
        "orderUpdateId": order_update_id,
        "lastNodeId": last_node_id,
        "lastNodeSequenceId": last_node_sequence_id,
        "nodeStates": node_states or [],
        "edgeStates": edge_states or [],
        "driving": driving,
        "actionStates": [],
        "instantActionStates": instant_action_states or [],
        "powerSupply": {"stateOfCharge": state_of_charge, "charging": False},
        "operatingMode": "AUTOMATIC",
        "errors": [],
        "safetyState": {"activeEmergencyStop": "NONE", "fieldViolation": False},
    }
    if mobile_robot_position is not None:
        payload["mobileRobotPosition"] = mobile_robot_position
    return payload


def build_factsheet_payload(identity: RobotIdentity, *, header_id: int) -> dict:
    return {
        "headerId": header_id,
        "timestamp": utc_timestamp(),
        "version": "3.0.0",
        "manufacturer": identity.manufacturer,
        "serialNumber": identity.serial_number,
        "typeSpecification": {
            "seriesName": "TARS Research Simulator",
            "mobileRobotKinematics": "DIFFERENTIAL",
            "mobileRobotClass": "CARRIER",
            "maximumLoadMass": 10.0,
            "localizationTypes": ["NATURAL"],
            "navigationTypes": ["FREELY_NAVIGATING"],
        },
        "physicalParameters": {
            "speedMin": 0.0,
            "speedMax": 1.0,
            "accelerationMax": 0.5,
            "decelerationMax": 0.5,
            "heightMin": 0.2,
            "heightMax": 0.2,
            "width": 0.4,
            "length": 0.6,
        },
        "protocolLimits": {},
        "protocolFeatures": {},
        "mobileRobotGeometry": {"envelopes2d": [], "envelopes3d": []},
        "loadSpecification": {"loadPositions": [], "loadSets": []},
    }
