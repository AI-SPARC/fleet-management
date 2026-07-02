from tars_robot_simulator.payloads import RobotIdentity
from tars_robot_simulator.simulator import SimulatedRobot


def test_simulated_robot_publishes_connection_factsheet_and_state() -> None:
    robot = SimulatedRobot(RobotIdentity("ResearchBot", "RB-SIM-001"))

    publications = robot.startup_publications()

    assert [publication.topic for publication in publications] == [
        "vda5050/v3/ResearchBot/RB-SIM-001/connection",
        "vda5050/v3/ResearchBot/RB-SIM-001/factsheet",
        "vda5050/v3/ResearchBot/RB-SIM-001/state",
    ]
    assert publications[0].qos == 1
    assert publications[0].retain is True
    assert publications[2].payload["powerSupply"]["stateOfCharge"] == 80.0


def test_simulated_robot_tracks_received_order_in_next_state() -> None:
    robot = SimulatedRobot(RobotIdentity("ResearchBot", "RB-SIM-001"))

    robot.apply_order({"orderId": "order-42", "orderUpdateId": 3, "nodes": [], "edges": []})
    publication = robot.state_publication()

    assert publication.payload["orderId"] == "order-42"
    assert publication.payload["orderUpdateId"] == 3


def test_simulated_robot_advances_through_order_node_positions() -> None:
    robot = SimulatedRobot(RobotIdentity("ResearchBot", "RB-SIM-001"))
    robot.apply_order(
        {
            "orderId": "order-42",
            "nodes": [
                {
                    "nodeId": "A",
                    "sequenceId": 0,
                    "released": True,
                    "nodePosition": {"x": 0, "y": 0, "theta": 0, "mapId": "lab"},
                },
                {
                    "nodeId": "B",
                    "sequenceId": 2,
                    "released": True,
                    "nodePosition": {"x": 5, "y": 2, "theta": 0, "mapId": "lab"},
                },
            ],
            "edges": [],
        }
    )

    first = robot.state_publication().payload
    second = robot.state_publication().payload

    assert first["lastNodeId"] == "A"
    assert first["driving"] is True
    assert first["mobileRobotPosition"]["mapId"] == "lab"
    assert second["lastNodeId"] == "B"
    assert second["driving"] is False
    assert second["nodeStates"] == []


def test_simulated_robot_clears_order_after_cancel_order_instant_action() -> None:
    robot = SimulatedRobot(RobotIdentity("ResearchBot", "RB-CANCEL"))
    robot.apply_order({"orderId": "order-42", "orderUpdateId": 3})

    robot.apply_instant_actions(
        {"actions": [{"actionId": "cancel-1", "actionType": "cancelOrder"}]}
    )

    publication = robot.state_publication()
    assert publication.payload["orderId"] == ""
    assert publication.payload["orderUpdateId"] == 0
    assert publication.payload["instantActionStates"] == [
        {"actionId": "cancel-1", "actionStatus": "FINISHED"}
    ]
