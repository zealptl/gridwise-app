import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  accessToken: string | null
  userId: string | null
  email: string | null
  isAuthenticated: boolean
  setAuth: (token: string, userId: string, email: string, accessToken?: string) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      accessToken: null,
      userId: null,
      email: null,
      isAuthenticated: false,
      setAuth: (token, userId, email, accessToken) => set({ token, accessToken: accessToken ?? null, userId, email, isAuthenticated: true }),
      clearAuth: () => set({ token: null, accessToken: null, userId: null, email: null, isAuthenticated: false }),
    }),
    { name: 'gridwise-auth' }
  )
)
