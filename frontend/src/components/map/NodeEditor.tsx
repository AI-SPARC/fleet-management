import { useState, type FormEvent } from 'react';

import type { MapNodeInput, MapPoint } from '../../api/client';
import { Button } from '../ui/button';

export function NodeEditor({
  disabled,
  initialPosition,
  onSubmit,
}: {
  disabled?: boolean;
  initialPosition?: MapPoint;
  onSubmit: (node: MapNodeInput) => Promise<unknown>;
}) {
  const [nodeKey, setNodeKey] = useState('');
  const [x, setX] = useState(String(initialPosition?.x ?? 0));
  const [y, setY] = useState(String(initialPosition?.y ?? 0));
  const [theta, setTheta] = useState('0');

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    await onSubmit({ nodeKey: nodeKey.trim(), x: Number(x), y: Number(y), theta: Number(theta) });
    setNodeKey('');
  };

  return (
    <form className="grid gap-3" onSubmit={submit}>
      <h3 className="m-0 text-sm font-semibold">Add node</h3>
      {initialPosition && (
        <p className="m-0 text-xs text-muted-foreground">Coordinates selected on the map.</p>
      )}
      <label className="grid gap-1 text-xs font-medium">
        Node ID
        <input className="h-9 rounded-md border bg-background px-3" onChange={(event) => setNodeKey(event.target.value)} required value={nodeKey} />
      </label>
      <div className="grid grid-cols-3 gap-2">
        <CoordinateInput label="X" onChange={setX} value={x} />
        <CoordinateInput label="Y" onChange={setY} value={y} />
        <CoordinateInput label="Theta" onChange={setTheta} value={theta} />
      </div>
      <Button disabled={disabled} size="sm" type="submit">Save node</Button>
    </form>
  );
}

function CoordinateInput({ label, onChange, value }: { label: string; onChange: (value: string) => void; value: string }) {
  return (
    <label className="grid gap-1 text-xs font-medium">
      {label}
      <input className="h-9 min-w-0 rounded-md border bg-background px-2" onChange={(event) => onChange(event.target.value)} required step="any" type="number" value={value} />
    </label>
  );
}
