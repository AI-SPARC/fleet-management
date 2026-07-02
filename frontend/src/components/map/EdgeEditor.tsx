import { useState, type FormEvent } from 'react';

import type { MapEdgeInput, MapNode } from '../../api/client';
import { Button } from '../ui/button';

export function EdgeEditor({
  nodes,
  disabled,
  onSubmit,
}: {
  nodes: MapNode[];
  disabled?: boolean;
  onSubmit: (edge: MapEdgeInput) => Promise<unknown>;
}) {
  const [edgeKey, setEdgeKey] = useState('');
  const [fromNodeKey, setFromNodeKey] = useState('');
  const [toNodeKey, setToNodeKey] = useState('');
  const [distance, setDistance] = useState('');
  const [bidirectional, setBidirectional] = useState(false);

  const resolvedFromNodeKey = nodes.some((node) => node.nodeKey === fromNodeKey)
    ? fromNodeKey
    : nodes[0]?.nodeKey ?? '';
  const resolvedToNodeKey = nodes.some((node) => node.nodeKey === toNodeKey)
    ? toNodeKey
    : nodes[1]?.nodeKey ?? nodes[0]?.nodeKey ?? '';
  const fromNode = nodes.find((node) => node.nodeKey === resolvedFromNodeKey);
  const toNode = nodes.find((node) => node.nodeKey === resolvedToNodeKey);
  const suggestedDistance =
    fromNode && toNode
      ? String(Math.round(Math.hypot(toNode.x - fromNode.x, toNode.y - fromNode.y) * 1000) / 1000)
      : '';
  const resolvedDistance = distance || suggestedDistance;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    await onSubmit({
      edgeKey: edgeKey.trim(),
      fromNodeKey: resolvedFromNodeKey,
      toNodeKey: resolvedToNodeKey,
      distance: Number(resolvedDistance),
      bidirectional,
    });
    setEdgeKey('');
    setDistance('');
  };

  return (
    <form className="grid gap-3" onSubmit={submit}>
      <h3 className="m-0 text-sm font-semibold">Add edge</h3>
      <label className="grid gap-1 text-xs font-medium">
        Edge ID
        <input className="h-9 rounded-md border bg-background px-3" onChange={(event) => setEdgeKey(event.target.value)} required value={edgeKey} />
      </label>
      <div className="grid grid-cols-2 gap-2">
        <NodeSelect label="From" nodes={nodes} onChange={(value) => { setFromNodeKey(value); setDistance(''); }} value={resolvedFromNodeKey} />
        <NodeSelect label="To" nodes={nodes} onChange={(value) => { setToNodeKey(value); setDistance(''); }} value={resolvedToNodeKey} />
      </div>
      <label className="grid gap-1 text-xs font-medium">
        Distance
        <input className="h-9 rounded-md border bg-background px-3" min="0.001" onChange={(event) => setDistance(event.target.value)} required step="any" type="number" value={resolvedDistance} />
        <span className="text-[0.68rem] text-muted-foreground">Suggested from node coordinates; edit to override.</span>
      </label>
      <label className="flex items-center gap-2 text-xs font-medium">
        <input checked={bidirectional} onChange={(event) => setBidirectional(event.target.checked)} type="checkbox" />
        Bidirectional
      </label>
      <Button disabled={disabled || nodes.length < 2 || resolvedFromNodeKey === resolvedToNodeKey} size="sm" type="submit">Save edge</Button>
    </form>
  );
}

function NodeSelect({ label, nodes, onChange, value }: { label: string; nodes: MapNode[]; onChange: (value: string) => void; value: string }) {
  return (
    <label className="grid gap-1 text-xs font-medium">
      {label}
      <select className="h-9 min-w-0 rounded-md border bg-background px-2" onChange={(event) => onChange(event.target.value)} required value={value}>
        <option value="">Select</option>
        {nodes.map((node) => <option key={node.id} value={node.nodeKey}>{node.nodeKey}</option>)}
      </select>
    </label>
  );
}
