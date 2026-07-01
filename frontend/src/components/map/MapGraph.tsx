import { mapBackgroundUrl, type FleetMapDetail, type Robot, type RobotState } from '../../api/client';
import { worldToPixel } from './mapGeometry';

export type RobotMapPosition = {
  robot: Robot;
  state: RobotState;
};

export function MapGraph({
  map,
  robots,
  highlightedNodeKeys = [],
}: {
  map: FleetMapDetail;
  robots: RobotMapPosition[];
  highlightedNodeKeys?: string[];
}) {
  const positions = [
    ...map.nodes.map((node) => ({ x: node.x, y: node.y })),
    ...robots.flatMap(({ state }) => {
      const position = state.agvPosition;
      return isPosition(position) ? [{ x: position.x, y: position.y }] : [];
    }),
  ];
  const background = map.background;
  const calibration = background?.calibration;
  const project = calibration
    ? (x: number, y: number) => worldToPixel({ x, y }, calibration)
    : createProjection(positions);
  const canvasWidth = calibration ? background.width : 900;
  const canvasHeight = calibration ? background.height : 480;
  const visualScale = Math.max(canvasWidth / 900, canvasHeight / 480);
  const nodesByKey = new Map(map.nodes.map((node) => [node.nodeKey, node]));
  const highlighted = new Set(highlightedNodeKeys);

  return (
    <svg
      aria-label={`Graph map ${map.name}`}
      className="h-[480px] w-full rounded-2xl border bg-card"
      role="img"
      viewBox={`0 0 ${canvasWidth} ${canvasHeight}`}
    >
      <defs>
        <marker
          id="edge-arrow"
          markerHeight={7 * visualScale}
          markerWidth={7 * visualScale}
          orient="auto"
          refX={6 * visualScale}
          refY={3.5 * visualScale}
        >
          <polygon
            fill="#777"
            points={`0 0, ${7 * visualScale} ${3.5 * visualScale}, 0 ${7 * visualScale}`}
          />
        </marker>
      </defs>
      {calibration && (
        <image
          data-map-background
          height={background.height}
          href={mapBackgroundUrl(map.id, background.updatedAt)}
          opacity="0.72"
          width={background.width}
          x="0"
          y="0"
        />
      )}
      <g>
        {map.edges.map((edge) => {
          const start = nodesByKey.get(edge.fromNodeKey);
          const end = nodesByKey.get(edge.toNodeKey);
          if (!start || !end) return null;
          const from = project(start.x, start.y);
          const to = project(end.x, end.y);
          const onRoute = highlighted.has(start.nodeKey) && highlighted.has(end.nodeKey);
          return (
            <line
              data-edge-key={edge.edgeKey}
              key={edge.id}
              markerEnd="url(#edge-arrow)"
              stroke={onRoute ? '#111' : '#aaa'}
              strokeWidth={(onRoute ? 3 : 1.5) * visualScale}
              x1={from.x}
              x2={to.x}
              y1={from.y}
              y2={to.y}
            />
          );
        })}
      </g>
      <g>
        {map.nodes.map((node) => {
          const point = project(node.x, node.y);
          return (
            <g data-node-key={node.nodeKey} key={node.id} transform={`translate(${point.x} ${point.y})`}>
              <circle
                fill={highlighted.has(node.nodeKey) ? '#111' : '#fff'}
                r={11 * visualScale}
                stroke="#111"
                strokeWidth={2 * visualScale}
              />
              <text
                fill="#111"
                fontSize={12 * visualScale}
                fontWeight="600"
                textAnchor="middle"
                y={-18 * visualScale}
              >
                {node.nodeKey}
              </text>
            </g>
          );
        })}
      </g>
      <g>
        {robots.map(({ robot, state }) => {
          const position = state.agvPosition;
          if (!isPosition(position) || position.mapId !== map.id) return null;
          const point = project(position.x, position.y);
          return (
            <g data-robot-id={robot.id} key={robot.id} transform={`translate(${point.x} ${point.y})`}>
              <rect
                fill="#111"
                height={18 * visualScale}
                rx={4 * visualScale}
                transform="rotate(45)"
                width={18 * visualScale}
                x={-9 * visualScale}
                y={-9 * visualScale}
              />
              <text
                fill="#111"
                fontSize={11 * visualScale}
                fontWeight="700"
                textAnchor="middle"
                y={27 * visualScale}
              >
                {robot.displayName || robot.serialNumber}
              </text>
            </g>
          );
        })}
      </g>
      {map.nodes.length === 0 && (
        <text
          fill="#777"
          fontSize={14 * visualScale}
          textAnchor="middle"
          x={canvasWidth / 2}
          y={canvasHeight / 2}
        >
          Add the first node to start this graph.
        </text>
      )}
    </svg>
  );
}

function isPosition(value: unknown): value is { x: number; y: number; mapId: string } {
  if (typeof value !== 'object' || value === null) return false;
  const position = value as Record<string, unknown>;
  return (
    typeof position.x === 'number' &&
    typeof position.y === 'number' &&
    typeof position.mapId === 'string'
  );
}

function createProjection(positions: Array<{ x: number; y: number }>) {
  const xs = positions.map(({ x }) => x);
  const ys = positions.map(({ y }) => y);
  const minX = Math.min(...xs, 0);
  const maxX = Math.max(...xs, 1);
  const minY = Math.min(...ys, 0);
  const maxY = Math.max(...ys, 1);
  const scale = Math.min(800 / Math.max(maxX - minX, 1), 380 / Math.max(maxY - minY, 1));
  return (x: number, y: number) => ({
    x: 50 + (x - minX) * scale,
    y: 430 - (y - minY) * scale,
  });
}
