import { create } from 'zustand'
import type { FantasyTeam, TeamSummary } from '@/types/team'

interface TeamState {
  teams: TeamSummary[]
  currentTeam: FantasyTeam | null
  loading: boolean
  error: string | null

  setTeams: (teams: TeamSummary[]) => void
  setCurrentTeam: (team: FantasyTeam | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
}

export const useTeamStore = create<TeamState>((set) => ({
  teams: [],
  currentTeam: null,
  loading: false,
  error: null,

  setTeams: (teams) => set({ teams }),
  setCurrentTeam: (team) => set({ currentTeam: team }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}))
