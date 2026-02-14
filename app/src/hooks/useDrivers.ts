import { useState, useEffect } from 'react'
import { driversApi } from '@/api/drivers'
import type { Driver } from '@/types/driver'

export const useDrivers = (filters?: { team_name?: string; status?: string }) => {
  const [drivers, setDrivers] = useState<Driver[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchDrivers = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await driversApi.getAll(filters)
        setDrivers(data)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to fetch drivers')
      } finally {
        setLoading(false)
      }
    }

    fetchDrivers()
  }, [filters?.team_name, filters?.status])

  return { drivers, loading, error }
}
