import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import type { TeamSummary } from '@/types/team'
import { Link } from 'react-router-dom'
import { CheckCircle, XCircle, Eye, Pencil } from 'lucide-react'

interface TeamCardProps {
  team: TeamSummary
}

export const TeamCard = ({ team }: TeamCardProps) => {
  const budgetPercentage = (team.budget_used / 100) * 100

  return (
    <Card className="group transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          {/* Team Name - Primary Hierarchy */}
          <CardTitle className="text-xl font-semibold leading-tight">
            {team.team_name}
          </CardTitle>

          {/* Status Badge - Unmissable, High Contrast */}
          <Badge
            variant={team.is_valid ? 'default' : 'destructive'}
            className="shrink-0 flex items-center gap-1.5 px-2.5 py-1"
          >
            {team.is_valid ? (
              <>
                <CheckCircle className="h-3.5 w-3.5" aria-hidden="true" />
                <span>Valid</span>
              </>
            ) : (
              <>
                <XCircle className="h-3.5 w-3.5" aria-hidden="true" />
                <span>Invalid</span>
              </>
            )}
          </Badge>
        </div>

        {/* Season - Secondary Info */}
        <p className="text-sm text-muted-foreground mt-1">Season {team.season}</p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Budget - Visual Progress (Not Just Numbers) */}
        <div className="space-y-2">
          <div className="flex items-baseline justify-between">
            <span className="text-xs font-medium text-muted-foreground">Budget</span>
            <span className="text-sm font-semibold">
              {team.budget_used.toFixed(1)}M / 100M
            </span>
          </div>
          <Progress
            value={budgetPercentage}
            className="h-2"
            aria-label={`Budget usage: ${budgetPercentage}%`}
          />
        </div>

        {/* Team Composition - Compact Grid */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Drivers</span>
            <span className="font-medium">{team.driver_count}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Constructors</span>
            <span className="font-medium">{team.constructor_count}</span>
          </div>
        </div>

        {/* Actions - Clear Separation, Equal Weight */}
        <div className="flex gap-2 pt-2 border-t">
          <Button
            asChild
            variant="outline"
            size="sm"
            className="flex-1"
          >
            <Link to={`/teams/${team.team_id}`}>
              <Eye className="h-4 w-4 mr-1.5" aria-hidden="true" />
              View
            </Link>
          </Button>
          <Button
            asChild
            size="sm"
            className="flex-1"
          >
            <Link to={`/teams/${team.team_id}/edit`}>
              <Pencil className="h-4 w-4 mr-1.5" aria-hidden="true" />
              Edit
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
