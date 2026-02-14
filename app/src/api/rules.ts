import apiClient from './client'
import type { Rule, RuleCreate, RuleUpdate, RuleType } from '@/types/rule'

export const rulesApi = {
  getAll: async (params?: {
    is_active?: boolean
    rule_type?: RuleType
  }): Promise<Rule[]> => {
    const response = await apiClient.get('/rules', { params })
    return response.data
  },

  getById: async (ruleId: string): Promise<Rule> => {
    const response = await apiClient.get(`/rules/${ruleId}`)
    return response.data
  },

  create: async (data: RuleCreate): Promise<Rule> => {
    const response = await apiClient.post('/rules', data)
    return response.data
  },

  update: async (ruleId: string, data: RuleUpdate): Promise<Rule> => {
    const response = await apiClient.put(`/rules/${ruleId}`, data)
    return response.data
  },

  delete: async (ruleId: string): Promise<void> => {
    await apiClient.delete(`/rules/${ruleId}`)
  },

  toggle: async (ruleId: string): Promise<Rule> => {
    const response = await apiClient.patch(`/rules/${ruleId}/toggle`)
    return response.data
  },
}
