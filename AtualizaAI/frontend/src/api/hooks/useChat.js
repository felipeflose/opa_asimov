import { useMutation } from '@tanstack/react-query';
import apiClient from '../client';

export function useChat() {
  return useMutation({
    mutationFn: async ({ message, history, image_path }) => {
      const { data } = await apiClient.post('/api/chat/', {
        message,
        history,
        image_path
      });
      return data;
    },
    // Aqui não invalidamos queries pois o chat é um stream de estado local
  });
}
