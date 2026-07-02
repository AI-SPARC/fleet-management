from app.db.base import Mission
from app.services.mission_status_service import infer_mission_status


def mission(status: str = "sent") -> Mission:
    return Mission(
        id="mission-1",
        assigned_robot_id="robot-1",
        start_node_key="A",
        goal_node_key="B",
        status=status,
        priority=0,
    )


def test_matching_order_moves_sent_mission_to_running() -> None:
    assert infer_mission_status(
        mission(),
        {
            "orderId": "mission-1",
            "lastNodeId": "A",
            "nodeStates": [{"nodeId": "B"}],
            "edgeStates": [],
            "driving": True,
            "errors": [],
        },
    ) == "running"


def test_consumed_route_at_goal_completes_mission() -> None:
    assert infer_mission_status(
        mission("running"),
        {
            "orderId": "mission-1",
            "lastNodeId": "B",
            "nodeStates": [],
            "edgeStates": [],
            "driving": False,
            "errors": [],
        },
    ) == "completed"


def test_fatal_robot_error_fails_active_mission() -> None:
    assert infer_mission_status(
        mission("running"),
        {"orderId": "mission-1", "errors": [{"errorLevel": "FATAL"}]},
    ) == "failed"
