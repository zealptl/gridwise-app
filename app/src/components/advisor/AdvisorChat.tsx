import { useEffect, useRef, useState } from 'react'
import { Loader2, Send } from 'lucide-react'
import { TeamRecommendationCard } from './TeamRecommendationCard'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

interface Props {
  sessionId: string
}

function getAuthHeader(): Record<string, string> {
  try {
    const stored = localStorage.getItem('gridwise-auth')
    if (stored) {
      const { state } = JSON.parse(stored)
      if (state?.token) return { Authorization: `Bearer ${state.token}` }
    }
  } catch {/* ignore */}
  return {}
}

export function AdvisorChat({ sessionId }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hi! I'm your F1 Fantasy Advisor. Ask me for a team recommendation for the upcoming race.",
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [recommendation, setRecommendation] = useState<Record<string, unknown> | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, recommendation])

  const send = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    const userId = crypto.randomUUID()
    const assistantId = crypto.randomUUID()

    setMessages(prev => [
      ...prev,
      { id: userId, role: 'user', content: userMessage },
      { id: assistantId, role: 'assistant', content: '' },
    ])

    try {
      const res = await fetch('/api/v1/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
        body: JSON.stringify({
          threadId: sessionId,
          runId: crypto.randomUUID(),
          messages: [{ id: userId, role: 'user', content: userMessage }],
        }),
      })

      if (!res.ok || !res.body) {
        throw new Error(`HTTP ${res.status}`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const lines = buf.split('\n')
        buf = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const evt = JSON.parse(line.slice(6))
            if (evt.type === 'TEXT_MESSAGE_CONTENT') {
              setMessages(prev =>
                prev.map(m =>
                  m.id === assistantId ? { ...m, content: m.content + evt.delta } : m
                )
              )
            } else if (
              evt.type === 'STATE_SNAPSHOT' &&
              evt.snapshot?.display_team_recommendation
            ) {
              setRecommendation(evt.snapshot.display_team_recommendation)
            }
          } catch {/* ignore malformed lines */}
        }
      }
    } catch {
      setMessages(prev =>
        prev.map(m =>
          m.id === assistantId
            ? { ...m, content: 'Sorry, something went wrong. Please try again.' }
            : m
        )
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map(m => (
          <div
            key={m.id}
            className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 text-sm whitespace-pre-wrap ${
                m.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              {m.content || (
                loading && m.role === 'assistant' && (
                  <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
                )
              )}
            </div>
          </div>
        ))}

        {recommendation && (
          <div className="flex justify-start">
            <TeamRecommendationCard
              recommendation={recommendation as Parameters<typeof TeamRecommendationCard>[0]['recommendation']}
              status="complete"
            />
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t bg-white px-4 py-3 flex items-center gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder="Ask for a team recommendation…"
          disabled={loading}
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          className="rounded-md bg-blue-600 p-2 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
