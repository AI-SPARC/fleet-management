import { useState } from 'react';

import type { MapObstacle, MapPoint } from '../../api/client';
import { Button } from '../ui/button';

export function ObstacleEditor({
  obstacles,
  draftPoints,
  drawing,
  canDraw,
  disabled,
  onStart,
  onUndo,
  onCancel,
  onSave,
  onDelete,
}: {
  obstacles: MapObstacle[];
  draftPoints: MapPoint[];
  drawing: boolean;
  canDraw: boolean;
  disabled?: boolean;
  onStart: () => void;
  onUndo: () => void;
  onCancel: () => void;
  onSave: (name: string, safetyMargin: number) => Promise<unknown>;
  onDelete: (obstacleId: string) => void;
}) {
  const [name, setName] = useState('Obstacle');
  const [safetyMargin, setSafetyMargin] = useState('0');

  return (
    <section className="grid gap-3 border-t pt-6">
      <div>
        <h3 className="m-0 text-sm font-semibold">Obstacle areas</h3>
        <p className="mb-0 mt-1 text-xs text-muted-foreground">
          Draw a polygon. Edges within the robot corridor become unavailable.
        </p>
      </div>
      {!drawing ? (
        <Button disabled={disabled || !canDraw} onClick={onStart} size="sm" type="button" variant="outline">
          Draw obstacle
        </Button>
      ) : (
        <div className="grid gap-3 rounded-xl border p-3">
          <p className="m-0 text-xs text-muted-foreground">
            Click at least three points on the calibrated map. Selected: {draftPoints.length}
          </p>
          <label className="grid gap-1 text-xs font-medium">
            Name
            <input
              className="h-9 rounded-md border bg-background px-2"
              onChange={(event) => setName(event.target.value)}
              value={name}
            />
          </label>
          <label className="grid gap-1 text-xs font-medium">
            Extra safety margin (m)
            <input
              className="h-9 rounded-md border bg-background px-2"
              min="0"
              onChange={(event) => setSafetyMargin(event.target.value)}
              step="any"
              type="number"
              value={safetyMargin}
            />
          </label>
          <div className="flex flex-wrap gap-2">
            <Button disabled={draftPoints.length === 0} onClick={onUndo} size="sm" type="button" variant="outline">
              Undo point
            </Button>
            <Button onClick={onCancel} size="sm" type="button" variant="outline">
              Cancel
            </Button>
            <Button
              disabled={disabled || draftPoints.length < 3 || !name.trim()}
              onClick={() => onSave(name.trim(), Number(safetyMargin))}
              size="sm"
              type="button"
            >
              Save area
            </Button>
          </div>
        </div>
      )}
      {obstacles.length > 0 && (
        <ul className="m-0 grid list-none gap-2 p-0">
          {obstacles.map((obstacle) => (
            <li className="flex items-center justify-between gap-2 text-xs" key={obstacle.id}>
              <span>
                {obstacle.name} · {obstacle.points.length} points
              </span>
              <Button
                disabled={disabled}
                onClick={() => onDelete(obstacle.id)}
                size="sm"
                type="button"
                variant="ghost"
              >
                Remove
              </Button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
