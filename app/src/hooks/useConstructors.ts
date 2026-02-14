import { useState, useEffect } from 'react'
import { constructorsApi } from '@/api/constructors'
import type { Constructor } from '@/types/constructor'

export const useConstructors = (filters?: { status?: string }) => {
  const [constructors, setConstructors] = useState<Constructor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchConstructors = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await constructorsApi.getAll(filters)
        setConstructors(data)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to fetch constructors')
      } finally {
        setLoading(false)
      }
    }

    fetchConstructors()
  }, [filters?.status])

  return { constructors, loading, error }
}
