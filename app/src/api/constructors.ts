import apiClient from './client'
import type { Constructor, ConstructorCreate, ConstructorUpdate } from '@/types/constructor'

export const constructorsApi = {
  getAll: async (params?: {
    status?: string
    skip?: number
    limit?: number
  }): Promise<Constructor[]> => {
    const response = await apiClient.get('/constructors', { params })
    return response.data
  },

  getById: async (constructorId: string): Promise<Constructor> => {
    const response = await apiClient.get(`/constructors/${constructorId}`)
    return response.data
  },

  create: async (data: ConstructorCreate): Promise<Constructor> => {
    const response = await apiClient.post('/constructors', data)
    return response.data
  },

  update: async (constructorId: string, data: ConstructorUpdate): Promise<Constructor> => {
    const response = await apiClient.put(`/constructors/${constructorId}`, data)
    return response.data
  },

  delete: async (constructorId: string): Promise<void> => {
    await apiClient.delete(`/constructors/${constructorId}`)
  },
}
