import { describe, expect, it } from 'vitest';

import { worldToPixel } from './mapGeometry';

describe('map calibration geometry', () => {
  it('projects metric coordinates into calibrated image pixels', () => {
    expect(
      worldToPixel(
        { x: 4, y: 2 },
        {
          metersPerPixel: 0.02,
          originPixelX: 100,
          originPixelY: 300,
          rotationDegrees: 0,
        },
      ),
    ).toEqual({ x: 300, y: 200 });
  });
});
