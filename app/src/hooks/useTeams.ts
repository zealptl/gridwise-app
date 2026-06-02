import { useEffect, useCallback } from 'react'
import { teamsApi } from '@/api/teams'
import { useTeamStore } from '@/stores/teamStore'

export const useTeams = (filters?: {
  season?: number
  is_valid?: boolean
  skip?: number
  limit?: number
}) => {
  const { teams, setTeams, loading, setLoading, error, setError } = useTeamStore()
  const { season, is_valid, skip, limit } = filters ?? {}

  const fetchTeams = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await teamsApi.getAll({ season, is_valid, skip, limit })
      setTeams(data.teams)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch teams')
    } finally {
      setLoading(false)
    }
  }, [season, is_valid, skip, limit, setTeams, setLoading, setError])

  useEffect(() => {
    fetchTeams()
  }, [fetchTeams])

  return { teams, loading, error, refetch: fetchTeams }
}
