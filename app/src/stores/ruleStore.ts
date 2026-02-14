import { create } from 'zustand'
import type { Rule } from '@/types/rule'

interface RuleState {
  rules: Rule[]
  activeRules: Rule[]
  loading: boolean
  error: string | null

  setRules: (rules: Rule[]) => void
  setActiveRules: (rules: Rule[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useRuleStore = create<RuleState>((set) => ({
  rules: [],
  activeRules: [],
  loading: false,
  error: null,

  setRules: (rules) => set({ rules }),
  setActiveRules: (rules) => set({ activeRules: rules }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}))
