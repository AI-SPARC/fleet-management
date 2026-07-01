from math import isclose

import pytest

from app.services.map_background_service import (
    Point,
    calculate_calibration,
    world_to_pixel,
)


def test_calibration_maps_world_coordinates_to_image_pixels() -> None:
    calibration = calculate_calibration(
        Point(100, 300), Point(600, 300), Point(0, 0), Point(10, 0)
    )

    assert isclose(calibration.meters_per_pixel, 0.02)
    assert isclose(calibration.origin_pixel_x, 100)
    assert isclose(calibration.origin_pixel_y, 300)
    assert isclose(calibration.rotation_degrees, 0)
    projected = world_to_pixel(Point(4, 2), calibration)
    assert isclose(projected.x, 300)
    assert isclose(projected.y, 200)


def test_calibration_supports_a_rotated_world_axis() -> None:
    calibration = calculate_calibration(
        Point(100, 100), Point(600, 100), Point(0, 0), Point(0, 10)
    )

    assert isclose(calibration.rotation_degrees, 90)
    projected = world_to_pixel(Point(0, 10), calibration)
    assert isclose(projected.x, 600)
    assert isclose(projected.y, 100)


def test_calibration_rejects_coincident_points() -> None:
    with pytest.raises(ValueError, match="non-zero distance"):
        calculate_calibration(Point(1, 1), Point(1, 1), Point(0, 0), Point(1, 0))
