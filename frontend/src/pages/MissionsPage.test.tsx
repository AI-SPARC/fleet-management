import '@testing-library/jest-dom/vitest';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createMemoryHistory, createRouter, RouterProvider } from '@tanstack/react-router';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { apiClient } from '../api/client';
import { routeTree } from '../app/router';

class FakeWebSocket {
  addEventListener() {}
  close() {}
}

describe('MissionsPage', () => {
  beforeEach(() => {
    vi.stubGlobal('WebSocket', FakeWebSocket);
    vi.stubGlobal('scrollTo', vi.fn());
    vi.spyOn(apiClient, 'listMaps').mockResolvedValue([
      { id: 'map-1', name: 'Lab', description: null },
    ]);
    vi.spyOn(apiClient, 'getMap').mockResolvedValue({
      id: 'map-1',
      name: 'Lab',
      description: null,
      background: null,
      nodes: [
        { id: 'node-a', nodeKey: 'A', x: 0, y: 0, theta: 0, nodeType: 'waypoint' },
        { id: 'node-b', nodeKey: 'B', x: 1, y: 0, theta: 0, nodeType: 'waypoint' },
      ],
      edges: [
        {
          id: 'edge-a-b',
          edgeKey: 'A-B',
          fromNodeKey: 'A',
          toNodeKey: 'B',
          distance: 1,
          bidirectional: false,
        },
      ],
    });
    vi.spyOn(apiClient, 'listRobots').mockResolvedValue([
      {
        id: 'robot-1',
        manufacturer: 'ResearchBot',
        serialNumber: 'RB001',
        displayName: 'Picker',
        protocolVersion: '3.0.0',
        lastConnectionState: 'ONLINE',
      },
    ]);
    vi.spyOn(apiClient, 'listMissions').mockResolvedValue([
      {
        id: 'mission-1',
        mapId: 'map-1',
        assignedRobotId: 'robot-1',
        startNodeKey: 'A',
        goalNodeKey: 'B',
        status: 'assigned',
        priority: 2,
      },
    ]);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('previews, creates, and dispatches a mission with order output', async () => {
    const previewRoute = vi
      .spyOn(apiClient, 'previewRoute')
      .mockResolvedValue({ nodeKeys: ['A', 'B'] });
    const createMission = vi.spyOn(apiClient, 'createMission').mockResolvedValue({
      id: 'mission-2',
      mapId: 'map-1',
      assignedRobotId: 'robot-1',
      startNodeKey: 'A',
      goalNodeKey: 'B',
      status: 'assigned',
      priority: 0,
    });
    const dispatchMission = vi.spyOn(apiClient, 'dispatchMission').mockResolvedValue({
      accepted: true,
      topic: 'vda5050/v3/ResearchBot/RB001/order',
      payload: { orderId: 'mission-1', nodes: [{ nodeId: 'A' }, { nodeId: 'B' }] },
      errors: [],
    });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const router = createRouter({
      routeTree,
      history: createMemoryHistory({ initialEntries: ['/missions'] }),
    });
    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    );

    expect(await screen.findByRole('heading', { name: 'Missions' })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText('Start node')).toHaveValue('A'));
    fireEvent.click(screen.getByRole('button', { name: 'Preview route' }));
    await waitFor(() => expect(previewRoute).toHaveBeenCalledWith('map-1', 'A', 'B'));
    expect(await screen.findAllByText('A → B')).toHaveLength(2);

    fireEvent.click(screen.getByRole('button', { name: 'Create mission' }));
    await waitFor(() =>
      expect(createMission).toHaveBeenCalledWith({
        mapId: 'map-1',
        assignedRobotId: 'robot-1',
        startNodeKey: 'A',
        goalNodeKey: 'B',
        priority: 0,
      }),
    );

    fireEvent.click(screen.getByRole('button', { name: 'Dispatch' }));
    await waitFor(() => expect(dispatchMission).toHaveBeenCalledWith('mission-1'));
    expect(await screen.findByText('vda5050/v3/ResearchBot/RB001/order')).toBeInTheDocument();
    expect(screen.getByText(/"orderId": "mission-1"/)).toBeInTheDocument();
  });
});
