import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/agents');
      return data;
    },
    // Cache de 60 segundos antes de considerar obsoleto
    staleTime: 60 * 1000,
  });
}

export function useSaveAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (agentData) => {
      const { data } = await apiClient.post('/api/agents/', agentData);
      return data;
    },
    onSuccess: () => {
      // Invalida a lista de agentes para forçar o refetch e atualizar a UI
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}

export function useDeleteAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (name) => {
      await apiClient.delete(`/api/agents/${name}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}
