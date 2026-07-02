export const queryKeys = {
  health: ['health'] as const,
  robots: {
    all: ['robots'] as const,
    detail: (robotId: string) => ['robots', robotId] as const,
    state: (robotId: string) => ['robots', robotId, 'state'] as const,
    factsheet: (robotId: string) => ['robots', robotId, 'factsheet'] as const,
  },
  maps: {
    all: ['maps'] as const,
    detail: (mapId: string) => ['maps', mapId] as const,
  },
  missions: {
    all: ['missions'] as const,
    detail: (missionId: string) => ['missions', missionId] as const,
    route: (missionId: string) => ['missions', missionId, 'route'] as const,
    trajectory: (missionId: string) => ['missions', missionId, 'trajectory'] as const,
  },
  mqtt: {
    all: ['mqtt-messages'] as const,
    list: (filters: Record<string, unknown>) => ['mqtt-messages', filters] as const,
  },
};
