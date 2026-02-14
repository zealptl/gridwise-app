import apiClient from './client'
import type { FantasyTeam, TeamCreate, TeamUpdate, PaginatedTeamsResponse } from '@/types/team'

export const teamsApi = {
  getAll: async (params?: {
    created_by?: string
    season?: number
    is_valid?: boolean
    is_active?: boolean
    skip?: number
    limit?: number
  }): Promise<PaginatedTeamsResponse> => {
    const response = await apiClient.get('/teams', { params })
    return response.data
  },

  getById: async (teamId: string): Promise<FantasyTeam> => {
    const response = await apiClient.get(`/teams/${teamId}`)
    return response.data
  },

  create: async (data: TeamCreate): Promise<FantasyTeam> => {
    const response = await apiClient.post('/teams', data)
    return response.data
  },

  update: async (teamId: string, data: TeamUpdate): Promise<FantasyTeam> => {
    const response = await apiClient.put(`/teams/${teamId}`, data)
    return response.data
  },
}
