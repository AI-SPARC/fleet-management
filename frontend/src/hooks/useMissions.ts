import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient, type MissionInput } from '../api/client';
import { queryKeys } from '../api/queryKeys';

export function useMissions() {
  return useQuery({
    queryKey: queryKeys.missions.all,
    queryFn: apiClient.listMissions,
  });
}

export function useMission(missionId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.missions.detail(missionId ?? ''),
    queryFn: () => apiClient.getMission(missionId as string),
    enabled: Boolean(missionId),
  });
}

export function useMissionRoute(
  missionId: string | undefined,
  mapId: string | null | undefined,
  startNodeKey: string | undefined,
  goalNodeKey: string | undefined,
) {
  return useQuery({
    queryKey: queryKeys.missions.route(missionId ?? ''),
    queryFn: () =>
      apiClient.previewRoute(mapId as string, startNodeKey as string, goalNodeKey as string),
    enabled: Boolean(missionId && mapId && startNodeKey && goalNodeKey),
    retry: false,
  });
}

export function useCreateMission() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: MissionInput) => apiClient.createMission(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.missions.all }),
  });
}

export function useDispatchMission() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (missionId: string) => apiClient.dispatchMission(missionId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.missions.all });
      void queryClient.invalidateQueries({ queryKey: queryKeys.mqtt.all });
    },
  });
}
