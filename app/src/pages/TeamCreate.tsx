import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import { DriverSelector } from '@/components/teams/DriverSelector'
import { ConstructorSelector } from '@/components/teams/ConstructorSelector'
import { DrsBoostSelector } from '@/components/teams/DrsBoostSelector'
import { BudgetDisplay } from '@/components/teams/BudgetDisplay'
import { ValidationErrors } from '@/components/teams/ValidationErrors'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { useDrivers } from '@/hooks/useDrivers'
import { useConstructors } from '@/hooks/useConstructors'
import { useBudgetCalculator } from '@/hooks/useBudgetCalculator'
import { useTeamValidation } from '@/hooks/useTeamValidation'
import { teamsApi } from '@/api/teams'
import type { Driver } from '@/types/driver'
import type { Constructor } from '@/types/constructor'
import { ArrowLeft, Save } from 'lucide-react'

export default function TeamCreate() {
  const navigate = useNavigate()
  const { toast } = useToast()

  const [teamName, setTeamName] = useState('')
  const [selectedDrivers, setSelectedDrivers] = useState<Driver[]>([])
  const [selectedConstructors, setSelectedConstructors] = useState<Constructor[]>([])
  const [drsBoostDriverId, setDrsBoostDriverId] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const { drivers, loading: driversLoading, error: driversError } = useDrivers({ status: 'active' })
  const { constructors, loading: constructorsLoading, error: constructorsError } = useConstructors({ status: 'active' })

  const { budgetUsed, budgetRemaining, isOverBudget } = useBudgetCalculator({
    selectedDrivers,
    selectedConstructors,
    budgetCap: 100.0,
  })

  const { isValid, errors } = useTeamValidation({
    selectedDrivers,
    selectedConstructors,
    drsBoostDriverId,
    budgetRemaining,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!teamName.trim()) {
      toast({
        title: 'Team name required',
        description: 'Please enter a name for your team',
        variant: 'destructive',
      })
      return
    }

    if (!isValid) {
      toast({
        title: 'Form incomplete',
        description: 'Please complete all required fields',
        variant: 'destructive',
      })
      return
    }

    try {
      setSubmitting(true)
      const team = await teamsApi.create({
        team_name: teamName,
        driver_ids: selectedDrivers.map((d) => d.driver_id),
        constructor_ids: selectedConstructors.map((c) => c.constructor_id),
        drs_boost_driver_id: drsBoostDriverId!,
        season: 2026,
      })

      toast({
        title: 'Team created!',
        description: `${teamName} is ready to race`,
      })

      navigate(`/teams/${team.team_id}`)
    } catch (err: any) {
      toast({
        title: 'Failed to create team',
        description: err.response?.data?.detail || 'Something went wrong. Please try again.',
        variant: 'destructive',
      })
    } finally {
      setSubmitting(false)
    }
  }

  // Loading State
  if (driversLoading || constructorsLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
        <p className="text-muted-foreground mt-4">Loading players...</p>
      </div>
    )
  }

  // Error State
  if (driversError || constructorsError) {
    return (
      <ErrorDisplay
        message={driversError || constructorsError || 'Failed to load data'}
      />
    )
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
      {/* Page Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/')}
          className="gap-2 hover:scale-105 transition-transform"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">Create New Team</h1>
          <p className="text-muted-foreground mt-1">
            Select your drivers and constructors within the 100M budget
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Team Name - First Focus */}
        <Card className="shadow-sm hover:shadow-md transition-shadow duration-200">
          <CardContent className="pt-6">
            <div className="space-y-2 max-w-md">
              <Label htmlFor="team-name" className="text-base font-medium">
                Team Name
              </Label>
              <Input
                id="team-name"
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                placeholder="Enter a name for your team"
                className="text-lg"
                maxLength={50}
                required
                autoFocus
              />
              <p className="text-sm text-muted-foreground">
                Choose a unique name that represents your team
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Validation Errors - Show Early */}
        <ValidationErrors errors={errors} />

        {/* Main Form Grid - Responsive */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - Budget & DRS (Sticky on Desktop) */}
          <div className="lg:col-span-1 space-y-6">
            <BudgetDisplay
              budgetUsed={budgetUsed}
              budgetRemaining={budgetRemaining}
              budgetCap={100.0}
              isOverBudget={isOverBudget}
            />
            <DrsBoostSelector
              selectedDrivers={selectedDrivers}
              drsBoostDriverId={drsBoostDriverId}
              onDrsBoostChange={setDrsBoostDriverId}
            />
          </div>

          {/* Main Selection Area */}
          <div className="lg:col-span-3 space-y-6">
            <DriverSelector
              drivers={drivers}
              selectedDrivers={selectedDrivers}
              onSelectionChange={setSelectedDrivers}
              maxSelection={5}
            />
            <ConstructorSelector
              constructors={constructors}
              selectedConstructors={selectedConstructors}
              onSelectionChange={setSelectedConstructors}
              maxSelection={2}
            />
          </div>
        </div>

        {/* Form Actions - Clear Hierarchy */}
        <div className="flex items-center gap-4 pt-6 border-t">
          <Button
            type="submit"
            disabled={!isValid || submitting}
            size="lg"
            className="min-w-[200px] shadow-sm hover:shadow-md transition-all duration-200"
          >
            {submitting ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Creating...
              </>
            ) : (
              <>
                <Save className="h-5 w-5 mr-2" />
                Create Team
              </>
            )}
          </Button>
          <Button
            type="button"
            variant="outline"
            size="lg"
            onClick={() => navigate('/')}
            disabled={submitting}
            className="hover:scale-105 transition-transform duration-200"
          >
            Cancel
          </Button>

          {/* Progress Indicator */}
          <div className="ml-auto text-sm text-muted-foreground">
            {isValid ? (
              <span className="text-green-600 font-medium animate-in fade-in duration-300">✓ Ready to create</span>
            ) : (
              <span>Complete all fields to continue</span>
            )}
          </div>
        </div>
      </form>
    </div>
  )
}
