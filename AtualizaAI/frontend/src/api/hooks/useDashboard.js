import { useQuery } from '@tanstack/react-query';
import apiClient from '../client';

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      // O BFF agrega os dados do dashboard em uma única chamada v3
      const { data } = await apiClient.get('/api/finops/summary');
      return data;
    },
    refetchInterval: 30 * 1000, // Sync automático a cada 30s as per spec
  });
}
