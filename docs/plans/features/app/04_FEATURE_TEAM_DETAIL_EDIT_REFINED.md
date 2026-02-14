# Feature: Team Detail & Edit Pages (Design-Refined)

## Overview

Build team detail view and edit functionality with transfer tracking and penalty calculation.

**Estimated Time:** 3-4 hours
**Dependencies:** Foundation + Dashboard + Team Creation
**Complexity:** Medium-High

---

## Design Philosophy

Detail pages tell a story. This page answers: "What's my team? How is it performing? What can I change?" The edit page is high-stakes — transfers have penalties. Make the consequences crystal clear before the user clicks "Save." No surprises.

### Design Principles Applied
- **Information Architecture:** Details are scannable — most important info above the fold
- **Transfer Feedback:** Penalty warnings are unmissable, not hidden in fine print
- **Visual Comparison:** Edit mode shows what changed, not just final state
- **Confirmation Clarity:** User sees exact penalty before confirming
- **Responsive Layout:** Sidebar for history on desktop, stacked on mobile
- **State Transitions:** Moving between detail → edit → detail feels smooth

---

## Feature Requirements

### Functional Requirements

**Team Detail Page:**
- Display complete team information
- Show all selected drivers with DRS boost indicator
- Show all selected constructors
- Display budget breakdown
- Show validation status and errors
- Display transfer history
- Navigation to edit page

**Team Edit Page:**
- Pre-populate form with existing team data
- Track changes from original team
- Calculate transfer count
- Show transfer warnings (when exceeding free transfers)
- Display penalty calculation (-10 points per excess transfer)
- Update team via API
- Redirect to detail page on success

### Business Rules
- 2 free transfers per race
- -10 points penalty for each transfer beyond 2
- Transfer = any change (driver/constructor added or removed)
- DRS boost changes don't count as transfers

### Design Requirements
- **Detail View:** Team status is hero element, driver list is scannable, history is accessible but not intrusive
- **Edit Mode:** Changes are highlighted, transfer count is persistent, penalty warning is impossible to miss
- **Transfer Tracking:** Visual diff shows what's changing (added=green, removed=red)
- **Confirmation:** Submit button shows exact consequence ("Save & Accept -20 Points")
- **History:** Timeline format, most recent first, penalties clearly marked
- **Responsive:** Sidebar collapses to accordion on mobile

---

## Design System Tokens Required

Add these to `DESIGN_SYSTEM.md`:

```yaml
# Status Colors
status-valid-bg: hsl(142, 76%, 96%)
status-valid-border: hsl(142, 76%, 40%)
status-invalid-bg: hsl(0, 84%, 96%)
status-invalid-border: hsl(0, 84%, 60%)

# Transfer States
transfer-added: hsl(142, 76%, 40%)      # Green - new selection
transfer-removed: hsl(0, 84%, 60%)      # Red - removed selection
transfer-neutral: hsl(var(--muted))     # Gray - unchanged

# Warning Levels
warning-info: hsl(199, 89%, 48%)        # Blue - informational
warning-caution: hsl(38, 92%, 50%)      # Amber - warning
warning-danger: hsl(0, 84%, 60%)        # Red - critical

# Timeline
timeline-dot-size: 12px
timeline-line-width: 2px
timeline-spacing: 24px
```

---

## Implementation Steps

### Step 1: Enhanced TeamDetailView Component

**File:** `src/components/teams/TeamDetailView.tsx`

**Design Notes:**
- Hero section: Team name + validation badge (impossible to miss)
- Budget summary uses visual progress (not just numbers)
- Player lists are scannable (name, team, price in consistent layout)
- DRS boost indicator is prominent (lightning bolt + yellow accent)
- Validation errors are clear but not shouty

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { FantasyTeam } from '@/types/team'
import { CheckCircle, XCircle, Zap, Users, Building2, Wallet } from 'lucide-react'

interface TeamDetailProps {
  team: FantasyTeam
}

export const TeamDetailView = ({ team }: TeamDetailProps) => {
  const budgetPercentage = (team.budget_used / team.budget_cap) * 100

  return (
    <div className="space-y-6">
      {/* Hero Section - Team Name & Status */}
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">{team.team_name}</h2>
            <p className="text-lg text-muted-foreground mt-1">Season {team.season}</p>
          </div>
          <Badge
            variant={team.is_valid ? 'default' : 'destructive'}
            className="text-base px-4 py-2 flex items-center gap-2"
          >
            {team.is_valid ? (
              <>
                <CheckCircle className="h-5 w-5" aria-hidden="true" />
                <span>Valid Team</span>
              </>
            ) : (
              <>
                <XCircle className="h-5 w-5" aria-hidden="true" />
                <span>Invalid Team</span>
              </>
            )}
          </Badge>
        </div>
      </div>

      {/* Budget Summary - Visual First */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <Wallet className="h-5 w-5" aria-hidden="true" />
            Budget Overview
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-xs text-muted-foreground mb-1">Cap</div>
              <div className="text-2xl font-bold tabular-nums">
                {team.budget_cap.toFixed(1)}M
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Used</div>
              <div className="text-2xl font-bold tabular-nums">
                {team.budget_used.toFixed(1)}M
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Remaining</div>
              <div className={`text-2xl font-bold tabular-nums ${team.budget_remaining < 0 ? 'text-red-600' : 'text-green-600'}`}>
                {team.budget_remaining.toFixed(1)}M
              </div>
            </div>
          </div>
          <Progress
            value={Math.min(budgetPercentage, 100)}
            className="h-3"
            indicatorClassName={budgetPercentage > 100 ? 'bg-red-600' : 'bg-green-600'}
          />
        </CardContent>
      </Card>

      {/* Drivers - Scannable List */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" aria-hidden="true" />
            Drivers
            <Badge variant="secondary" className="ml-auto">
              {team.drivers.length} / 5
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {team.drivers.map((driver) => {
              const hasDrsBoost = driver.driver_id === team.drs_boost_driver_id

              return (
                <div
                  key={driver.driver_id}
                  className={`
                    flex items-center justify-between p-3 rounded-lg border-2
                    ${hasDrsBoost ? 'border-yellow-400 bg-yellow-50' : 'border-border'}
                  `}
                >
                  <div className="flex items-center gap-3">
                    {hasDrsBoost && (
                      <Zap
                        className="h-5 w-5 text-yellow-600 fill-yellow-600"
                        aria-label="DRS Boost assigned"
                      />
                    )}
                    <div>
                      <div className="font-medium text-base">{driver.driver_name}</div>
                      <div className="text-sm text-muted-foreground">{driver.team_name}</div>
                    </div>
                  </div>
                  <div className="font-bold text-lg tabular-nums">{driver.price.toFixed(1)}M</div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Constructors - Scannable List */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" aria-hidden="true" />
            Constructors
            <Badge variant="secondary" className="ml-auto">
              {team.constructors.length} / 2
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {team.constructors.map((constructor) => (
              <div
                key={constructor.constructor_id}
                className="flex items-center justify-between p-3 rounded-lg border"
              >
                <div className="font-medium text-base">{constructor.constructor_name}</div>
                <div className="font-bold text-lg tabular-nums">{constructor.price.toFixed(1)}M</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Validation Errors - Clear but Not Shouty */}
      {!team.is_valid && team.validation_errors.length > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="text-red-900 flex items-center gap-2">
              <XCircle className="h-5 w-5" />
              Team Issues
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {team.validation_errors.map((error, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-red-800">
                  <span className="mt-0.5">•</span>
                  <span>{error.message}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
```

### Step 2: Enhanced TransferHistory Component

**File:** `src/components/teams/TransferHistory.tsx`

**Design Notes:**
- Timeline format (visual, scannable)
- Penalties are immediately visible (red badge)
- Most recent first
- Empty state guides user

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TransferRecord } from '@/types/team'
import { Calendar, TrendingDown } from 'lucide-react'
import { format } from 'date-fns'

interface TransferHistoryProps {
  transfers: TransferRecord[]
}

export const TransferHistory = ({ transfers }: TransferHistoryProps) => {
  if (transfers.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Calendar className="h-5 w-5" aria-hidden="true" />
            Transfer History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <TrendingDown className="h-12 w-12 text-muted-foreground mx-auto mb-3 opacity-50" />
            <p className="text-sm text-muted-foreground">No transfers yet</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Calendar className="h-5 w-5" aria-hidden="true" />
          Transfer History
          <Badge variant="secondary" className="ml-auto">
            {transfers.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {transfers.map((transfer, index) => (
            <div
              key={index}
              className="relative pl-6 pb-4 border-l-2 border-muted last:border-l-0 last:pb-0"
            >
              {/* Timeline Dot */}
              <div className="absolute left-0 top-0 -translate-x-[7px] w-3 h-3 rounded-full bg-primary border-2 border-background" />

              {/* Transfer Details */}
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <time className="text-sm font-medium">
                    {format(new Date(transfer.timestamp), 'MMM d, yyyy')}
                  </time>
                  {transfer.penalty_points > 0 && (
                    <Badge variant="destructive" className="flex items-center gap-1">
                      {transfer.penalty_points} points
                    </Badge>
                  )}
                </div>

                <div className="text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">
                    {transfer.transfers_used}
                  </span>{' '}
                  {transfer.transfers_used === 1 ? 'transfer' : 'transfers'} used
                  {transfer.transfers_available > 0 && (
                    <span className="text-muted-foreground">
                      {' '}· {transfer.transfers_available} available
                    </span>
                  )}
                </div>

                {transfer.changes && transfer.changes.length > 0 && (
                  <div className="text-xs text-muted-foreground space-y-1 mt-2">
                    {transfer.changes.map((change, idx) => (
                      <div key={idx} className="flex items-start gap-1.5">
                        <span>→</span>
                        <span>{JSON.stringify(change)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
```

### Step 3: Enhanced TeamDetail Page

**File:** `src/pages/TeamDetail.tsx`

**Design Notes:**
- Page header has back button + edit action
- Two-column layout on desktop (detail + history sidebar)
- Single column on mobile (stacked)
- Loading state preserves layout

```typescript
import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { TeamDetailView } from '@/components/teams/TeamDetailView'
import { TransferHistory } from '@/components/teams/TransferHistory'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { teamsApi } from '@/api/teams'
import { FantasyTeam } from '@/types/team'
import { ArrowLeft, Pencil } from 'lucide-react'

export default function TeamDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [team, setTeam] = useState<FantasyTeam | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchTeam = async () => {
      if (!id) return

      try {
        setLoading(true)
        const data = await teamsApi.getById(id)
        setTeam(data)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load team')
      } finally {
        setLoading(false)
      }
    }

    fetchTeam()
  }, [id])

  // Loading State
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
        <p className="text-muted-foreground mt-4">Loading team...</p>
      </div>
    )
  }

  // Error State
  if (error || !team) {
    return <ErrorDisplay message={error || 'Team not found'} />
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Page Header - Clear Actions */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/')}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Teams
        </Button>
        <div className="flex-1" />
        <Button asChild size="lg" className="gap-2">
          <Link to={`/teams/${id}/edit`}>
            <Pencil className="h-5 w-5" />
            Edit Team
          </Link>
        </Button>
      </div>

      {/* Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - Team Details */}
        <div className="lg:col-span-2">
          <TeamDetailView team={team} />
        </div>

        {/* Sidebar - Transfer History */}
        <div>
          <TransferHistory transfers={team.transfer_history} />
        </div>
      </div>
    </div>
  )
}
```

### Step 4: Enhanced TeamEdit Page with Transfer Warning

**File:** `src/pages/TeamEdit.tsx`

**Design Notes:**
- Transfer count is always visible (sticky card on mobile, sidebar on desktop)
- Penalty warning is unmissable (large, red, shows exact calculation)
- Changed selections are highlighted (green=added, red=removed, subtle icons)
- Submit button text changes based on penalty ("Save Changes" vs "Save & Accept -20 Points")
- Confirmation feels high-stakes but clear

```typescript
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/components/ui/use-toast'
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
import { Driver } from '@/types/driver'
import { Constructor } from '@/types/constructor'
import { FantasyTeam } from '@/types/team'
import { AlertTriangle, Save, ArrowLeft, TrendingDown } from 'lucide-react'

export default function TeamEdit() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()

  const [team, setTeam] = useState<FantasyTeam | null>(null)
  const [selectedDrivers, setSelectedDrivers] = useState<Driver[]>([])
  const [selectedConstructors, setSelectedConstructors] = useState<Constructor[]>([])
  const [drsBoostDriverId, setDrsBoostDriverId] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const [originalDriverIds, setOriginalDriverIds] = useState<string[]>([])
  const [originalConstructorIds, setOriginalConstructorIds] = useState<string[]>([])

  const { drivers, loading: driversLoading } = useDrivers({ status: 'active' })
  const { constructors, loading: constructorsLoading } = useConstructors({ status: 'active' })

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

  // Calculate transfers
  const calculateTransfers = () => {
    const currentDriverIds = selectedDrivers.map(d => d.driver_id)
    const currentConstructorIds = selectedConstructors.map(c => c.constructor_id)

    const driversAdded = currentDriverIds.filter(id => !originalDriverIds.includes(id)).length
    const driversRemoved = originalDriverIds.filter(id => !currentDriverIds.includes(id)).length
    const constructorsAdded = currentConstructorIds.filter(id => !originalConstructorIds.includes(id)).length
    const constructorsRemoved = originalConstructorIds.filter(id => !currentConstructorIds.includes(id)).length

    return driversAdded + driversRemoved + constructorsAdded + constructorsRemoved
  }

  const transfers = calculateTransfers()
  const freeTransfers = 2
  const excessTransfers = Math.max(0, transfers - freeTransfers)
  const penaltyPoints = excessTransfers * -10

  // Load team data
  useEffect(() => {
    const fetchTeam = async () => {
      if (!id) return

      try {
        const data = await teamsApi.getById(id)
        setTeam(data)

        const driverIds = data.drivers.map(d => d.driver_id)
        const constructorIds = data.constructors.map(c => c.constructor_id)
        setOriginalDriverIds(driverIds)
        setOriginalConstructorIds(constructorIds)

        setDrsBoostDriverId(data.drs_boost_driver_id)
      } catch (err: any) {
        toast({
          title: 'Error loading team',
          description: err.response?.data?.detail || 'Failed to load team',
          variant: 'destructive',
        })
        navigate('/')
      }
    }

    fetchTeam()
  }, [id, toast, navigate])

  // Pre-populate selections
  useEffect(() => {
    if (!team || drivers.length === 0 || selectedDrivers.length > 0) return
    const teamDrivers = drivers.filter(d =>
      team.drivers.some(td => td.driver_id === d.driver_id)
    )
    setSelectedDrivers(teamDrivers)
  }, [team, drivers, selectedDrivers.length])

  useEffect(() => {
    if (!team || constructors.length === 0 || selectedConstructors.length > 0) return
    const teamConstructors = constructors.filter(c =>
      team.constructors.some(tc => tc.constructor_id === c.constructor_id)
    )
    setSelectedConstructors(teamConstructors)
  }, [team, constructors, selectedConstructors.length])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!isValid || !id) {
      toast({
        title: 'Form incomplete',
        description: 'Please complete all required fields',
        variant: 'destructive',
      })
      return
    }

    // High-stakes confirmation for penalties
    if (penaltyPoints < 0) {
      const confirmed = window.confirm(
        `You will receive a ${penaltyPoints} point penalty for ${excessTransfers} excess transfer${excessTransfers !== 1 ? 's' : ''}.\n\nAre you sure you want to continue?`
      )
      if (!confirmed) return
    }

    try {
      setSubmitting(true)
      await teamsApi.update(id, {
        driver_ids: selectedDrivers.map((d) => d.driver_id),
        constructor_ids: selectedConstructors.map((c) => c.constructor_id),
        drs_boost_driver_id: drsBoostDriverId!,
      })

      toast({
        title: 'Team updated!',
        description: penaltyPoints < 0
          ? `Changes saved with ${penaltyPoints} point penalty`
          : 'Changes saved successfully',
      })

      navigate(`/teams/${id}`)
    } catch (err: any) {
      toast({
        title: 'Failed to update team',
        description: err.response?.data?.detail || 'Something went wrong',
        variant: 'destructive',
      })
    } finally {
      setSubmitting(false)
    }
  }

  // Loading State
  if (!team || driversLoading || constructorsLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
        <p className="text-muted-foreground mt-4">Loading team...</p>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(`/teams/${id}`)}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">Edit Team</h1>
          <p className="text-lg text-muted-foreground mt-1">{team.team_name}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Transfer Warning - Unmissable */}
        {penaltyPoints < 0 && (
          <Alert variant="destructive" className="border-2 border-red-500">
            <AlertTriangle className="h-5 w-5" />
            <AlertTitle className="text-lg font-semibold">Transfer Penalty Warning</AlertTitle>
            <AlertDescription className="text-base space-y-2">
              <p>
                You have made <strong>{transfers} transfers</strong>. You will receive a{' '}
                <strong className="text-lg">{penaltyPoints} point penalty</strong>.
              </p>
              <div className="bg-red-100 rounded-md p-3 text-red-900 text-sm space-y-1">
                <div>Free transfers: {freeTransfers}</div>
                <div>Excess transfers: {excessTransfers}</div>
                <div className="font-semibold">Penalty: {excessTransfers} × -10 = {penaltyPoints} points</div>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Transfer Info - Positive Feedback */}
        {transfers > 0 && penaltyPoints === 0 && (
          <Alert className="border-green-500 bg-green-50">
            <TrendingDown className="h-5 w-5 text-green-700" />
            <AlertTitle className="text-green-900">Free Transfers</AlertTitle>
            <AlertDescription className="text-green-800">
              You have made {transfers} of {freeTransfers} free transfers. No penalty.
            </AlertDescription>
          </Alert>
        )}

        {/* No Changes Yet */}
        {transfers === 0 && (
          <Card>
            <CardContent className="py-4">
              <p className="text-sm text-muted-foreground text-center">
                Make changes to your team below. You have {freeTransfers} free transfers per race.
              </p>
            </CardContent>
          </Card>
        )}

        <ValidationErrors errors={errors} />

        {/* Main Form Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - Budget & DRS */}
          <div className="lg:col-span-1 space-y-6">
            <BudgetDisplay
              budgetUsed={budgetUsed}
              budgetRemaining={budgetRemaining}
              budgetCap={100.0}
              isOverBudget={isOverBudget}
            />

            {/* Transfer Counter - Sticky */}
            <Card className="sticky top-6">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <TrendingDown className="h-5 w-5" aria-hidden="true" />
                  Transfers
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Used</span>
                  <Badge variant={penaltyPoints < 0 ? 'destructive' : 'secondary'} className="text-base px-3 py-1">
                    {transfers}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Free</span>
                  <span className="font-medium">{freeTransfers}</span>
                </div>
                {excessTransfers > 0 && (
                  <div className="flex items-center justify-between pt-2 border-t">
                    <span className="text-sm font-medium text-red-700">Penalty</span>
                    <span className="font-bold text-lg text-red-700">{penaltyPoints}</span>
                  </div>
                )}
              </CardContent>
            </Card>

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

        {/* Form Actions - High Stakes */}
        <div className="flex items-center gap-4 pt-6 border-t">
          <Button
            type="submit"
            disabled={!isValid || submitting}
            size="lg"
            className={`min-w-[240px] ${penaltyPoints < 0 ? 'bg-red-600 hover:bg-red-700' : ''}`}
          >
            {submitting ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Saving...
              </>
            ) : penaltyPoints < 0 ? (
              <>
                <Save className="h-5 w-5 mr-2" />
                Save & Accept {penaltyPoints} Points
              </>
            ) : (
              <>
                <Save className="h-5 w-5 mr-2" />
                Save Changes
              </>
            )}
          </Button>
          <Button
            type="button"
            variant="outline"
            size="lg"
            onClick={() => navigate(`/teams/${id}`)}
            disabled={submitting}
          >
            Cancel
          </Button>

          {/* Status Indicator */}
          {transfers > 0 && (
            <div className="ml-auto text-sm">
              {penaltyPoints < 0 ? (
                <span className="text-red-700 font-medium">
                  {excessTransfers} excess transfer{excessTransfers !== 1 ? 's' : ''}
                </span>
              ) : (
                <span className="text-green-700 font-medium">
                  Within free transfers
                </span>
              )}
            </div>
          )}
        </div>
      </form>
    </div>
  )
}
```

---

## Design Testing Checklist

### Detail View
- [ ] Team name and status are hero elements (impossible to miss)
- [ ] Budget uses visual progress, not just numbers
- [ ] DRS boost indicator stands out (lightning + yellow)
- [ ] Player lists are scannable (consistent layout)
- [ ] Validation errors are clear but not alarming
- [ ] Transfer history is accessible but not intrusive

### Edit Mode
- [ ] Transfer count is always visible (sticky on mobile)
- [ ] Penalty warning is unmissable when > 2 transfers
- [ ] Penalty calculation is shown step-by-step
- [ ] Submit button text reflects consequence
- [ ] Confirmation dialog is clear about penalty
- [ ] Free transfer feedback is positive, not neutral

### Transfer Tracking
- [ ] Transfer count updates instantly
- [ ] Penalty calculation is accurate
- [ ] Changing only DRS = 0 transfers
- [ ] Adding 1 driver = 1 transfer
- [ ] Removing 1 driver = 1 transfer
- [ ] Swapping 1 driver = 2 transfers

### Responsive Design
- [ ] Mobile: Stacked layout, budget at top
- [ ] Desktop: Sidebar (sticky), main content area
- [ ] Transfer counter sticky on both mobile and desktop
- [ ] History sidebar collapses on mobile

### States & Feedback
- [ ] Loading shows spinner + message
- [ ] Success toast before redirect
- [ ] Error toast stays until dismissed
- [ ] Penalty warning has distinct visual treatment

---

## Acceptance Criteria

✅ **Feature is design-complete when:**

1. Detail view tells the team story clearly and completely
2. Transfer penalties are impossible to miss or misunderstand
3. Edit mode feels high-stakes but transparent
4. Transfer counter is always visible and accurate
5. Confirmation clearly states consequences
6. History is accessible and scannable
7. Responsive layout works on all devices
8. State transitions feel smooth
9. Accessibility passes keyboard + screen reader tests
10. User never feels surprised by a penalty

**The Jobs Test:**
- Does the user understand the penalty before clicking? → YES
- Can the user scan their team in < 5 seconds? → YES
- Does transfer history feel useful, not cluttered? → YES

---

## Definition of Done

- [ ] All design testing checklist items pass
- [ ] Transfer penalties tested at 0, 1, 2, 3, 5 transfers
- [ ] Penalty confirmation tested and clear
- [ ] Detail → Edit → Detail flow feels smooth
- [ ] History timeline renders correctly
- [ ] No TypeScript errors
- [ ] DESIGN_SYSTEM.md tokens used exclusively
- [ ] Accessibility tested
- [ ] Screenshots captured
- [ ] LESSONS.md updated

**Proceed to Rules Admin once complete.**
