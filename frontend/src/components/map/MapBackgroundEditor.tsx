import { useState, type ChangeEvent, type MouseEvent } from 'react';

import {
  mapBackgroundUrl,
  type MapBackground,
  type MapCalibrationInput,
  type MapPoint,
} from '../../api/client';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

export function MapBackgroundEditor({
  mapId,
  background,
  busy,
  onUpload,
  onCalibrate,
}: {
  mapId: string;
  background: MapBackground | null | undefined;
  busy: boolean;
  onUpload: (file: File) => Promise<unknown>;
  onCalibrate: (input: MapCalibrationInput) => Promise<unknown>;
}) {
  const [pixelPointA, setPixelPointA] = useState<MapPoint>();
  const [pixelPointB, setPixelPointB] = useState<MapPoint>();
  const [worldPointA, setWorldPointA] = useState<MapPoint>({ x: 0, y: 0 });
  const [worldPointB, setWorldPointB] = useState<MapPoint>({ x: 1, y: 0 });

  const upload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setPixelPointA(undefined);
    setPixelPointB(undefined);
    await onUpload(file);
    event.target.value = '';
  };

  const selectPixelPoint = (event: MouseEvent<SVGSVGElement>) => {
    if (!background) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    const point = {
      x: ((event.clientX - bounds.left) / bounds.width) * background.width,
      y: ((event.clientY - bounds.top) / bounds.height) * background.height,
    };
    if (!pixelPointA || pixelPointB) {
      setPixelPointA(point);
      setPixelPointB(undefined);
    } else {
      setPixelPointB(point);
    }
  };

  const saveCalibration = () => {
    if (!pixelPointA || !pixelPointB) return;
    return onCalibrate({ pixelPointA, pixelPointB, worldPointA, worldPointB });
  };

  return (
    <Card className="rounded-2xl bg-card/80 shadow-none">
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="text-lg">Map background & calibration</CardTitle>
          <p className="mb-0 mt-1 text-sm text-muted-foreground">
            Upload a floor plan, click two known points, then enter their metric coordinates.
          </p>
        </div>
        <label className="cursor-pointer rounded-md border bg-background px-3 py-2 text-sm font-medium">
          {background ? 'Replace image' : 'Upload image'}
          <input
            accept="image/png,image/jpeg"
            aria-label="Background image"
            className="sr-only"
            disabled={busy}
            onChange={upload}
            type="file"
          />
        </label>
      </CardHeader>
      {background && (
        <CardContent className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_300px]">
          <svg
            aria-label="Calibration image"
            className="max-h-[430px] w-full cursor-crosshair rounded-xl border bg-white"
            onClick={selectPixelPoint}
            role="img"
            viewBox={`0 0 ${background.width} ${background.height}`}
          >
            <image
              height={background.height}
              href={mapBackgroundUrl(mapId, background.updatedAt)}
              width={background.width}
            />
            {pixelPointA && <CalibrationMarker label="A" point={pixelPointA} />}
            {pixelPointB && <CalibrationMarker label="B" point={pixelPointB} />}
          </svg>
          <div className="grid content-start gap-4">
            <p className="m-0 text-xs text-muted-foreground">
              {pixelPointA
                ? pixelPointB
                  ? 'Points A and B selected. Click again to restart.'
                  : 'Point A selected. Click point B.'
                : 'Click point A on the image.'}
            </p>
            <WorldPointEditor label="World point A" onChange={setWorldPointA} value={worldPointA} />
            <WorldPointEditor label="World point B" onChange={setWorldPointB} value={worldPointB} />
            <Button disabled={busy || !pixelPointA || !pixelPointB} onClick={saveCalibration}>
              Save calibration
            </Button>
            <p className="m-0 text-xs text-muted-foreground">
              {background.calibration
                ? `Current scale: ${background.calibration.metersPerPixel.toPrecision(5)} m/pixel`
                : 'The graph overlay remains disabled until calibration is saved.'}
            </p>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

function CalibrationMarker({ label, point }: { label: string; point: MapPoint }) {
  return (
    <g transform={`translate(${point.x} ${point.y})`}>
      <circle fill="#fff" r="10" stroke="#111" strokeWidth="3" />
      <text fill="#111" fontSize="12" fontWeight="700" textAnchor="middle" y="4">
        {label}
      </text>
    </g>
  );
}

function WorldPointEditor({
  label,
  value,
  onChange,
}: {
  label: string;
  value: MapPoint;
  onChange: (value: MapPoint) => void;
}) {
  return (
    <fieldset className="grid grid-cols-2 gap-2 rounded-xl border p-3">
      <legend className="px-1 text-xs font-medium">{label}</legend>
      <CoordinateInput
        axis="X"
        onChange={(x) => onChange({ ...value, x })}
        value={value.x}
      />
      <CoordinateInput
        axis="Y"
        onChange={(y) => onChange({ ...value, y })}
        value={value.y}
      />
    </fieldset>
  );
}

function CoordinateInput({
  axis,
  value,
  onChange,
}: {
  axis: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="grid gap-1 text-xs">
      {axis} (m)
      <input
        className="h-9 min-w-0 rounded-md border bg-background px-2"
        onChange={(event) => onChange(Number(event.target.value))}
        step="any"
        type="number"
        value={value}
      />
    </label>
  );
}
