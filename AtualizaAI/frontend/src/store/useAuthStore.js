import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      adminEmail: null,
      isAuthenticated: false,
      login: (token, email) => set({ 
        token, 
        adminEmail: email, 
        isAuthenticated: true 
      }),
      logout: () => set({ 
        token: null, 
        adminEmail: null, 
        isAuthenticated: false 
      }),
    }),
    {
      name: 'flose-auth-v3', // Versão 3
      storage: createJSONStorage(() => sessionStorage), // Segurança: expira ao fechar a guia
    }
  )
)
