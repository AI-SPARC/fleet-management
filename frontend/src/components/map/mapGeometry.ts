import type { MapCalibration, MapPoint } from '../../api/client';

export function worldToPixel(point: MapPoint, calibration: MapCalibration): MapPoint {
  const rotation = (calibration.rotationDegrees * Math.PI) / 180;
  const cosine = Math.cos(rotation);
  const sine = Math.sin(rotation);
  return {
    x:
      calibration.originPixelX +
      (point.x * cosine + point.y * sine) / calibration.metersPerPixel,
    y:
      calibration.originPixelY +
      (point.x * sine - point.y * cosine) / calibration.metersPerPixel,
  };
}
