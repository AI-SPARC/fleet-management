export type Health = {
  status: string;
  service: string;
  vda5050_version: string;
};

export type Robot = {
  id: string;
  manufacturer: string;
  serialNumber: string;
  displayName: string | null;
  protocolVersion: string;
  lastConnectionState: string;
};

export type RobotState = {
  id?: string;
  robotId?: string;
  headerId?: number | null;
  orderId?: string | null;
  orderUpdateId?: number | null;
  lastNodeId?: string | null;
  lastNodeSequenceId?: number | null;
  batteryCharge?: number | null;
  operatingMode?: string | null;
  errors?: Array<Record<string, unknown>> | null;
  safetyState?: Record<string, unknown> | null;
  agvPosition?: Record<string, unknown> | null;
  rawPayload?: Record<string, unknown>;
  receivedAt?: string;
  [key: string]: unknown;
};

export type FleetMap = {
  id: string;
  name: string;
  description: string | null;
};

export type MapNode = {
  id: string;
  nodeKey: string;
  x: number;
  y: number;
  theta: number;
  nodeType: string;
};

export type MapEdge = {
  id: string;
  edgeKey: string;
  fromNodeKey: string;
  toNodeKey: string;
  distance: number;
  bidirectional: boolean;
  blocked: boolean;
  blockReasons: string[];
};

export type MapPoint = { x: number; y: number };

export type MapCalibration = {
  metersPerPixel: number;
  originPixelX: number;
  originPixelY: number;
  rotationDegrees: number;
};

export type MapBackground = {
  filename: string;
  contentType: string;
  width: number;
  height: number;
  updatedAt: string;
  calibration: MapCalibration | null;
};

export type MapCalibrationInput = {
  pixelPointA: MapPoint;
  pixelPointB: MapPoint;
  worldPointA: MapPoint;
  worldPointB: MapPoint;
};

export type MapObstacle = {
  id: string;
  name: string;
  points: MapPoint[];
  safetyMargin: number;
  active: boolean;
};

export type MapObstacleInput = Pick<MapObstacle, 'name' | 'points' | 'safetyMargin'>;

export type FleetMapDetail = FleetMap & {
  nodes: MapNode[];
  edges: MapEdge[];
  background: MapBackground | null;
  obstacles: MapObstacle[];
};

export type MapNodeInput = Pick<MapNode, 'nodeKey' | 'x' | 'y' | 'theta'>;
export type MapNodePositionInput = Pick<MapNode, 'x' | 'y'> & { theta?: number };
export type MapEdgeInput = Pick<
  MapEdge,
  'edgeKey' | 'fromNodeKey' | 'toNodeKey' | 'distance' | 'bidirectional'
>;

export type Mission = {
  id: string;
  mapId: string | null;
  assignedRobotId: string | null;
  startNodeKey: string;
  goalNodeKey: string;
  status: string;
  priority: number;
};

export type MissionInput = {
  mapId: string;
  assignedRobotId: string;
  startNodeKey: string;
  goalNodeKey: string;
  priority: number;
};

export type MissionTrajectoryPoint = {
  timestamp: string;
  x: number;
  y: number;
  theta: number;
  mapId: string;
  lastNodeId: string | null;
  batteryCharge: number | null;
};

export type MissionDispatchResponse = {
  accepted: boolean;
  topic: string;
  payload: Record<string, unknown>;
  errors: string[];
};

export type MqttMessage = {
  id: string;
  direction: 'inbound' | 'outbound';
  topic: string;
  qos: number;
  retain: boolean;
  robotId: string | null;
  messageType: string;
  payload: Record<string, unknown>;
  schemaValid: boolean;
  validationErrors: string[];
  createdAt: string;
};

export type Page<T> = {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
  pages: number;
};

export type MqttMessageFilters = {
  direction?: 'inbound' | 'outbound';
  messageType?: string;
  robotId?: string;
  schemaValid?: boolean;
  page?: number;
  pageSize?: number;
};

export type InstantActionResponse = {
  accepted: boolean;
  topic: string;
  payload: Record<string, unknown>;
  errors: string[];
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly details: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export type ApiClient = ReturnType<typeof createApiClient>;

export function createApiClient(baseUrl: string) {
  const normalizedBaseUrl = baseUrl.replace(/\/$/, '');

  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${normalizedBaseUrl}${path}`, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...init?.headers,
      },
    });
    if (!response.ok) {
      const details = await readResponseBody(response);
      throw new ApiError(errorMessage(details, response.status), response.status, details);
    }
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }

  return {
    getHealth: () => request<Health>('/health'),
    listRobots: () => request<Robot[]>('/robots'),
    getRobot: (robotId: string) =>
      request<Robot>(`/robots/${encodeURIComponent(robotId)}`),
    getRobotState: (robotId: string) =>
      request<RobotState>(`/robots/${encodeURIComponent(robotId)}/state/latest`),
    getRobotFactsheet: (robotId: string) =>
      request<Record<string, unknown>>(`/robots/${encodeURIComponent(robotId)}/factsheet`),
    sendInstantAction: (robotId: string, actionType: string) =>
      request<InstantActionResponse>(
        `/robots/${encodeURIComponent(robotId)}/instant-actions`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ actionType }),
        },
      ),
    listMaps: () => request<FleetMap[]>('/maps'),
    getMap: (mapId: string) => request<FleetMapDetail>(`/maps/${encodeURIComponent(mapId)}`),
    createMap: (input: { name: string; description?: string }) =>
      request<FleetMap>('/maps', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      }),
    uploadMapBackground: (mapId: string, file: File) =>
      request<MapBackground>(
        `/maps/${encodeURIComponent(mapId)}/background?filename=${encodeURIComponent(file.name)}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': file.type || 'application/octet-stream' },
          body: file,
        },
      ),
    calibrateMapBackground: (mapId: string, input: MapCalibrationInput) =>
      request<MapBackground>(`/maps/${encodeURIComponent(mapId)}/background/calibration`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      }),
    createMapObstacle: (mapId: string, input: MapObstacleInput) =>
      request<MapObstacle>(`/maps/${encodeURIComponent(mapId)}/obstacles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      }),
    deleteMapObstacle: (mapId: string, obstacleId: string) =>
      request<void>(
        `/maps/${encodeURIComponent(mapId)}/obstacles/${encodeURIComponent(obstacleId)}`,
        { method: 'DELETE' },
      ),
    addMapNode: (mapId: string, input: MapNodeInput) =>
      request<{ id: string; nodeKey: string }>(`/maps/${encodeURIComponent(mapId)}/nodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      }),
    updateMapNode: (mapId: string, nodeKey: string, input: MapNodePositionInput) =>
      request<MapNode>(
        `/maps/${encodeURIComponent(mapId)}/nodes/${encodeURIComponent(nodeKey)}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(input),
        },
      ),
    addMapEdge: (mapId: string, input: MapEdgeInput) =>
      request<{ id: string; edgeKey: string }>(`/maps/${encodeURIComponent(mapId)}/edges`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      }),
    previewRoute: (mapId: string, startNodeKey: string, goalNodeKey: string) =>
      request<{ nodeKeys: string[] }>(`/maps/${encodeURIComponent(mapId)}/route-preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ startNodeKey, goalNodeKey }),
      }),
    listMissions: () => request<Mission[]>('/missions'),
    getMission: (missionId: string) =>
      request<Mission>(`/missions/${encodeURIComponent(missionId)}`),
    getMissionTrajectory: (missionId: string) =>
      request<MissionTrajectoryPoint[]>(
        `/missions/${encodeURIComponent(missionId)}/trajectory`,
      ),
    createMission: (input: MissionInput) =>
      request<Mission>('/missions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      }),
    dispatchMission: (missionId: string) =>
      request<MissionDispatchResponse>(`/missions/${encodeURIComponent(missionId)}/dispatch`, {
        method: 'POST',
      }),
    listMqttMessages: (filters: MqttMessageFilters = {}) => {
      const query = new URLSearchParams();
      for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined) query.set(key, String(value));
      }
      const suffix = query.size > 0 ? `?${query.toString()}` : '';
      return request<Page<MqttMessage>>(`/mqtt/messages${suffix}`);
    },
  };
}

async function readResponseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) return response.json();
  const text = await response.text();
  return text || null;
}

function errorMessage(details: unknown, status: number): string {
  if (typeof details === 'object' && details !== null && 'detail' in details) {
    const detail = (details as { detail: unknown }).detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.join(', ');
  }
  if (typeof details === 'string' && details) return details;
  return `API request failed with status ${status}`;
}

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export const apiClient = createApiClient(API_BASE_URL);

export function mapBackgroundUrl(mapId: string, updatedAt?: string): string {
  const suffix = updatedAt ? `?updatedAt=${encodeURIComponent(updatedAt)}` : '';
  return `${API_BASE_URL.replace(/\/$/, '')}/maps/${encodeURIComponent(mapId)}/background/content${suffix}`;
}
