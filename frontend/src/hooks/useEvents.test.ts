import { QueryClient } from '@tanstack/react-query';
import { describe, expect, it } from 'vitest';

import { queryKeys } from '../api/queryKeys';
import { applyDomainEvent } from './useEvents';

describe('domain event cache synchronization', () => {
  it('stores live robot state and invalidates the fleet list', async () => {
    const queryClient = new QueryClient();
    queryClient.setQueryData(queryKeys.robots.all, []);

    applyDomainEvent(queryClient, {
      id: 'event-1',
      type: 'robot.state.updated',
      timestamp: '2026-06-29T20:00:00.000Z',
      robotId: 'robot-1',
      payload: {
        headerId: 10,
        batteryCharge: 75,
        mobileRobotPosition: { x: 2, y: 3, mapId: 'lab' },
      },
    });
    await Promise.resolve();

    expect(queryClient.getQueryData(queryKeys.robots.state('robot-1'))).toEqual({
      headerId: 10,
      batteryCharge: 75,
      mobileRobotPosition: { x: 2, y: 3, mapId: 'lab' },
      agvPosition: { x: 2, y: 3, mapId: 'lab' },
      receivedAt: '2026-06-29T20:00:00.000Z',
    });
    expect(queryClient.getQueryState(queryKeys.robots.all)?.isInvalidated).toBe(true);
  });

  it('invalidates mission and MQTT queries for their respective events', async () => {
    const queryClient = new QueryClient();
    queryClient.setQueryData(queryKeys.missions.all, []);
    queryClient.setQueryData(queryKeys.mqtt.all, { items: [] });

    applyDomainEvent(queryClient, {
      id: 'event-2',
      type: 'mission.dispatched',
      timestamp: '2026-06-29T20:00:00.000Z',
      missionId: 'mission-1',
      payload: { status: 'sent' },
    });
    applyDomainEvent(queryClient, {
      id: 'event-3',
      type: 'mqtt.message.received',
      timestamp: '2026-06-29T20:00:01.000Z',
      payload: { messageType: 'state' },
    });
    await Promise.resolve();

    expect(queryClient.getQueryState(queryKeys.missions.all)?.isInvalidated).toBe(true);
    expect(queryClient.getQueryState(queryKeys.mqtt.all)?.isInvalidated).toBe(true);
  });
});
