import { CheckCircle2, Loader2, Minus } from 'lucide-react'

interface AgentProgress {
  f1DataAgent?: 'working' | 'done'
  intelAgent?: 'working' | 'done'
  fantasyContextAgent?: 'working' | 'done'
}

interface Props {
  progress: AgentProgress | null
}

const AGENT_ROWS: { label: string; key: keyof AgentProgress }[] = [
  { label: 'F1 Data', key: 'f1DataAgent' },
  { label: 'Intel', key: 'intelAgent' },
  { label: 'Fantasy Context', key: 'fantasyContextAgent' },
]

export function AgentProgressPanel({ progress }: Props) {
  if (!progress) return null

  const statuses = AGENT_ROWS.map(row => progress[row.key])
  const hasAnySet = statuses.some(s => s !== undefined)
  if (!hasAnySet) return null

  const allDone = statuses.every(s => s === 'done')
  const title = allDone ? 'Data ready' : 'Gathering data…'

  return (
    <div className="mx-4 mb-3 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs">
      <p className="mb-1.5 font-medium text-gray-600">{title}</p>
      <div className="space-y-1">
        {AGENT_ROWS.map(({ label, key }) => {
          const status = progress[key]
          return (
            <div key={key} className="flex items-center gap-2">
              {status === 'working' ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-blue-500 shrink-0" />
              ) : status === 'done' ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-green-500 shrink-0" />
              ) : (
                <Minus className="h-3.5 w-3.5 text-gray-300 shrink-0" />
              )}
              <span className={status === 'done' ? 'text-gray-500' : 'text-gray-700'}>
                {label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
