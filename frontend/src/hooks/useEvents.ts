import { QueryClient, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

import { API_BASE_URL, RobotState } from '../api/client';
import { queryKeys } from '../api/queryKeys';

export type DomainEvent = {
  id: string;
  type: string;
  timestamp: string;
  robotId?: string;
  missionId?: string;
  payload: Record<string, unknown>;
};

export const EVENTS_URL =
  import.meta.env.VITE_WS_URL ?? `${API_BASE_URL.replace(/^http/, 'ws')}/events/ws`;

export function applyDomainEvent(queryClient: QueryClient, event: DomainEvent) {
  if (event.type === 'robot.state.updated' && event.robotId) {
    queryClient.setQueryData<RobotState>(
      queryKeys.robots.state(event.robotId),
      {
        ...event.payload,
        agvPosition: asRecord(
          event.payload.agvPosition ?? event.payload.mobileRobotPosition,
        ),
        receivedAt: event.timestamp,
      },
    );
  }
  if (event.type.startsWith('robot.')) {
    void queryClient.invalidateQueries({ queryKey: queryKeys.robots.all });
  }
  if (event.type.startsWith('mission.')) {
    void queryClient.invalidateQueries({ queryKey: queryKeys.missions.all });
  }
  if (event.type.startsWith('mqtt.') || event.type === 'vda.validation.failed') {
    void queryClient.invalidateQueries({ queryKey: queryKeys.mqtt.all });
  }
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return typeof value === 'object' && value !== null
    ? (value as Record<string, unknown>)
    : undefined;
}

export function useEvents({ enabled = true, url = EVENTS_URL, reconnectMs = 2_000 } = {}) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!enabled) return;
    let active = true;
    let socket: WebSocket | undefined;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;

    const connect = () => {
      socket = new WebSocket(url);
      socket.addEventListener('message', (message) => {
        try {
          applyDomainEvent(queryClient, JSON.parse(String(message.data)) as DomainEvent);
        } catch {
          // Ignore malformed messages and keep the event stream alive.
        }
      });
      socket.addEventListener('close', () => {
        if (active) reconnectTimer = setTimeout(connect, reconnectMs);
      });
    };

    connect();
    return () => {
      active = false;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [enabled, queryClient, reconnectMs, url]);
}
