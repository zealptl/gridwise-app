import { useState, useEffect } from 'react'
import apiClient from '@/api/client'
import { AdvisorChat } from '@/components/advisor/AdvisorChat'

export default function Advisor() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    apiClient
      .post('/agent/sessions')
      .then(res => setSessionId(res.data.session_id))
      .catch(() => setError('Failed to start advisor session. Please try again.'))
  }, [])

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-3">
          <p className="text-red-600 text-sm">{error}</p>
          <button
            onClick={() => { setError(null); window.location.reload() }}
            className="text-sm text-blue-600 hover:underline"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!sessionId) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-gray-500">Starting advisor…</p>
      </div>
    )
  }

  return <AdvisorChat sessionId={sessionId} />
}
