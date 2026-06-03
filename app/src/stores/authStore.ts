import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  userId: string | null
  email: string | null
  isAuthenticated: boolean
  setAuth: (token: string, userId: string, email: string) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userId: null,
      email: null,
      isAuthenticated: false,
      setAuth: (token, userId, email) => set({ token, userId, email, isAuthenticated: true }),
      clearAuth: () => set({ token: null, userId: null, email: null, isAuthenticated: false }),
    }),
    { name: 'gridwise-auth' }
  )
)
