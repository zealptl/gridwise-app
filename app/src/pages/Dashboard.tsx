import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { TeamCard } from '@/components/teams/TeamCard'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { EmptyState } from '@/components/common/EmptyState'
import { useTeams } from '@/hooks/useTeams'
import { PlusCircle, Layers } from 'lucide-react'

export default function Dashboard() {
  const [season, setSeason] = useState<number | undefined>(2026)
  const [isValid, setIsValid] = useState<boolean | undefined>(undefined)

  const { teams, loading, error, refetch } = useTeams({ season, is_valid: isValid })

  // Loading State - Skeleton preserves layout
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-64 bg-muted animate-pulse rounded" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-64 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  // Error State
  if (error) {
    return <ErrorDisplay message={error} onRetry={refetch} />
  }

  return (
    <div className="space-y-6">
      {/* Page Header - Clear Hierarchy */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">My Teams</h1>
        <Button asChild size="lg" className="shadow-sm">
          <Link to="/teams/create">
            <PlusCircle className="h-5 w-5 mr-2" aria-hidden="true" />
            Create Team
          </Link>
        </Button>
      </div>

      {/* Filters - Compact, Subordinate */}
      <div className="flex flex-wrap items-center gap-3">
        <Select
          value={season?.toString()}
          onValueChange={(v) => setSeason(Number(v))}
        >
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Season" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="2026">2026 Season</SelectItem>
            <SelectItem value="2025">2025 Season</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={isValid?.toString() || 'all'}
          onValueChange={(v) => {
            if (v === 'all') setIsValid(undefined)
            else setIsValid(v === 'true')
          }}
        >
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Teams</SelectItem>
            <SelectItem value="true">Valid Only</SelectItem>
            <SelectItem value="false">Invalid Only</SelectItem>
          </SelectContent>
        </Select>

        {teams.length > 0 && (
          <span className="text-sm text-muted-foreground ml-auto">
            {teams.length} {teams.length === 1 ? 'team' : 'teams'}
          </span>
        )}
      </div>

      {/* Team Grid or Empty State */}
      {teams.length === 0 ? (
        <EmptyState
          icon={Layers}
          title="No teams yet"
          description="Create your first fantasy team to get started"
          action={
            <Button asChild size="lg" className="mt-4">
              <Link to="/teams/create">
                <PlusCircle className="h-5 w-5 mr-2" />
                Create Your First Team
              </Link>
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {teams.map((team) => (
            <TeamCard key={team.team_id} team={team} />
          ))}
        </div>
      )}
    </div>
  )
}
