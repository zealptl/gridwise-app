import apiClient from './client'
import type { Driver, DriverCreate, DriverUpdate } from '@/types/driver'

export const driversApi = {
  getAll: async (params?: {
    team_name?: string
    status?: string
    skip?: number
    limit?: number
  }): Promise<Driver[]> => {
    const response = await apiClient.get('/drivers', { params })
    return response.data
  },

  getById: async (driverId: string): Promise<Driver> => {
    const response = await apiClient.get(`/drivers/${driverId}`)
    return response.data
  },

  create: async (data: DriverCreate): Promise<Driver> => {
    const response = await apiClient.post('/drivers', data)
    return response.data
  },

  update: async (driverId: string, data: DriverUpdate): Promise<Driver> => {
    const response = await apiClient.put(`/drivers/${driverId}`, data)
    return response.data
  },

  delete: async (driverId: string): Promise<void> => {
    await apiClient.delete(`/drivers/${driverId}`)
  },

  getByTeam: async (teamName: string): Promise<Driver[]> => {
    const response = await apiClient.get(`/drivers/team/${teamName}`)
    return response.data
  },
}
