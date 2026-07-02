from app.services.map_obstacle_service import (
    Point,
    segment_intersects_polygon_corridor,
    validate_polygon,
)


def test_edge_corridor_detects_obstacle_with_safety_clearance() -> None:
    polygon = [Point(4, 0.5), Point(6, 0.5), Point(6, 2), Point(4, 2)]

    assert segment_intersects_polygon_corridor(Point(0, 0), Point(10, 0), polygon, 0.6)
    assert not segment_intersects_polygon_corridor(Point(0, 0), Point(10, 0), polygon, 0.4)


def test_polygon_validation_rejects_collinear_points() -> None:
    try:
        validate_polygon([Point(0, 0), Point(1, 0), Point(2, 0)])
    except ValueError as exc:
        assert str(exc) == "Obstacle polygon must enclose an area"
    else:
        raise AssertionError("Expected invalid polygon")
