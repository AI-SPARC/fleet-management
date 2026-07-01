import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  apiClient,
  type MapCalibrationInput,
  type MapEdgeInput,
  type MapNodeInput,
  type MapNodePositionInput,
  type MapObstacleInput,
} from '../api/client';
import { queryKeys } from '../api/queryKeys';

export function useMaps() {
  return useQuery({
    queryKey: queryKeys.maps.all,
    queryFn: apiClient.listMaps,
  });
}

export function useMap(mapId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.maps.detail(mapId ?? ''),
    queryFn: () => apiClient.getMap(mapId as string),
    enabled: Boolean(mapId),
  });
}

export function useCreateMap() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: apiClient.createMap,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.maps.all }),
  });
}

export function useAddMapNode(mapId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: MapNodeInput) => apiClient.addMapNode(mapId as string, input),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.maps.detail(mapId ?? '') }),
  });
}

export function useAddMapEdge(mapId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: MapEdgeInput) => apiClient.addMapEdge(mapId as string, input),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.maps.detail(mapId ?? '') }),
  });
}

export function useUpdateMapNode(mapId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ nodeKey, position }: { nodeKey: string; position: MapNodePositionInput }) =>
      apiClient.updateMapNode(mapId as string, nodeKey, position),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.maps.detail(mapId ?? '') }),
  });
}

export function useUploadMapBackground(mapId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => apiClient.uploadMapBackground(mapId as string, file),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.maps.detail(mapId ?? '') }),
  });
}

export function useCalibrateMapBackground(mapId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: MapCalibrationInput) =>
      apiClient.calibrateMapBackground(mapId as string, input),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.maps.detail(mapId ?? '') }),
  });
}

export function useCreateMapObstacle(mapId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: MapObstacleInput) =>
      apiClient.createMapObstacle(mapId as string, input),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.maps.detail(mapId ?? '') }),
  });
}

export function useDeleteMapObstacle(mapId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (obstacleId: string) =>
      apiClient.deleteMapObstacle(mapId as string, obstacleId),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.maps.detail(mapId ?? '') }),
  });
}

export function useRoutePreview(mapId: string | undefined) {
  return useMutation({
    mutationFn: ({ startNodeKey, goalNodeKey }: { startNodeKey: string; goalNodeKey: string }) =>
      apiClient.previewRoute(mapId as string, startNodeKey, goalNodeKey),
  });
}
