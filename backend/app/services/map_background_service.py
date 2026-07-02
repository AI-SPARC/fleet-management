from dataclasses import dataclass
from io import BytesIO
from math import atan2, cos, degrees, hypot, radians, sin

from PIL import Image, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.base import MapBackground, MapLayout


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Calibration:
    meters_per_pixel: float
    origin_pixel_x: float
    origin_pixel_y: float
    rotation_degrees: float


class MapBackgroundService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

    async def upload(
        self, map_id: str, filename: str, content_type: str | None, image_data: bytes
    ) -> MapBackground:
        await self._ensure_map_exists(map_id)
        if not image_data:
            raise ValueError("Background image is empty")
        if len(image_data) > self.settings.map_background_max_bytes:
            raise ValueError("Background image exceeds the upload limit")

        width, height, detected_type = self._inspect_image(image_data)
        if width * height > self.settings.map_background_max_pixels:
            raise ValueError("Background image dimensions exceed the limit")
        if content_type and content_type not in {detected_type, "application/octet-stream"}:
            raise ValueError("Background image content type does not match its data")

        safe_filename = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].strip()
        if not safe_filename:
            safe_filename = f"map-background.{detected_type.split('/')[-1]}"
        safe_filename = (
            safe_filename.replace('"', "_").replace("\r", "_").replace("\n", "_")[:255]
        )

        background = await self.session.get(MapBackground, map_id)
        if background is None:
            background = MapBackground(map_id=map_id)
            self.session.add(background)
        background.filename = safe_filename
        background.content_type = detected_type
        background.image_data = image_data
        background.width = width
        background.height = height
        background.meters_per_pixel = None
        background.origin_pixel_x = None
        background.origin_pixel_y = None
        background.rotation_degrees = None
        await self.session.commit()
        await self.session.refresh(background)
        return background

    async def calibrate(
        self,
        map_id: str,
        pixel_point_a: Point,
        pixel_point_b: Point,
        world_point_a: Point,
        world_point_b: Point,
    ) -> MapBackground:
        background = await self.session.get(MapBackground, map_id)
        if background is None:
            raise ValueError("Map background not found")
        for point in (pixel_point_a, pixel_point_b):
            if not (0 <= point.x <= background.width and 0 <= point.y <= background.height):
                raise ValueError("Calibration pixel points must be inside the image")

        calibration = calculate_calibration(
            pixel_point_a, pixel_point_b, world_point_a, world_point_b
        )
        background.meters_per_pixel = calibration.meters_per_pixel
        background.origin_pixel_x = calibration.origin_pixel_x
        background.origin_pixel_y = calibration.origin_pixel_y
        background.rotation_degrees = calibration.rotation_degrees
        await self.session.commit()
        await self.session.refresh(background)
        return background

    async def delete(self, map_id: str) -> None:
        background = await self.session.get(MapBackground, map_id)
        if background is None:
            raise ValueError("Map background not found")
        await self.session.delete(background)
        await self.session.commit()

    async def _ensure_map_exists(self, map_id: str) -> None:
        if await self.session.get(MapLayout, map_id) is None:
            raise ValueError("Map not found")

    @staticmethod
    def _inspect_image(image_data: bytes) -> tuple[int, int, str]:
        try:
            with Image.open(BytesIO(image_data)) as image:
                width, height = image.size
                image_format = image.format
                image.verify()
        except (UnidentifiedImageError, OSError) as exc:
            raise ValueError("Background must be a valid PNG or JPEG image") from exc
        content_types = {"PNG": "image/png", "JPEG": "image/jpeg"}
        if image_format not in content_types:
            raise ValueError("Background must be a PNG or JPEG image")
        return width, height, content_types[image_format]


def calculate_calibration(
    pixel_point_a: Point,
    pixel_point_b: Point,
    world_point_a: Point,
    world_point_b: Point,
) -> Calibration:
    pixel_dx = pixel_point_b.x - pixel_point_a.x
    pixel_dy = pixel_point_b.y - pixel_point_a.y
    world_dx = world_point_b.x - world_point_a.x
    world_dy = world_point_b.y - world_point_a.y
    pixel_distance = hypot(pixel_dx, pixel_dy)
    world_distance = hypot(world_dx, world_dy)
    if pixel_distance < 1e-6 or world_distance < 1e-6:
        raise ValueError("Calibration points must define a non-zero distance")

    meters_per_pixel = world_distance / pixel_distance
    pixel_angle = atan2(pixel_dy, pixel_dx)
    world_angle = atan2(world_dy, world_dx)
    rotation = pixel_angle + world_angle
    cosine = cos(rotation)
    sine = sin(rotation)
    origin_pixel_x = pixel_point_a.x - (
        world_point_a.x * cosine + world_point_a.y * sine
    ) / meters_per_pixel
    origin_pixel_y = pixel_point_a.y - (
        world_point_a.x * sine - world_point_a.y * cosine
    ) / meters_per_pixel
    rotation_degrees = (degrees(rotation) + 180) % 360 - 180
    return Calibration(
        meters_per_pixel=meters_per_pixel,
        origin_pixel_x=origin_pixel_x,
        origin_pixel_y=origin_pixel_y,
        rotation_degrees=rotation_degrees,
    )


def world_to_pixel(point: Point, calibration: Calibration) -> Point:
    rotation = radians(calibration.rotation_degrees)
    cosine = cos(rotation)
    sine = sin(rotation)
    return Point(
        x=calibration.origin_pixel_x
        + (point.x * cosine + point.y * sine) / calibration.meters_per_pixel,
        y=calibration.origin_pixel_y
        + (point.x * sine - point.y * cosine) / calibration.meters_per_pixel,
    )
