# Feature: Team Detail & Edit Pages

## Overview

Build team detail view and edit functionality with transfer tracking and penalty calculation.

**Estimated Time:** 3-4 hours
**Dependencies:** Foundation + Dashboard + Team Creation
**Complexity:** Medium-High

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

---

## Implementation Steps

### Step 1: Create TeamDetailView Component

**File:** `src/components/teams/TeamDetailView.tsx`

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { FantasyTeam } from '@/types/team'
import { CheckCircle, XCircle, Zap } from 'lucide-react'

interface TeamDetailProps {
  team: FantasyTeam
}

export const TeamDetailView = ({ team }: TeamDetailProps) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{team.team_name}</h2>
          <p className="text-muted-foreground">Season {team.season}</p>
        </div>
        <Badge variant={team.is_valid ? 'default' : 'destructive'} className="text-lg px-4 py-2">
          {team.is_valid ? (
            <><CheckCircle className="h-4 w-4 mr-2" /> Valid</>
          ) : (
            <><XCircle className="h-4 w-4 mr-2" /> Invalid</>
          )}
        </Badge>
      </div>

      {/* Budget Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Budget Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold">{team.budget_cap.toFixed(1)}M</div>
              <div className="text-sm text-muted-foreground">Cap</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{team.budget_used.toFixed(1)}M</div>
              <div className="text-sm text-muted-foreground">Used</div>
            </div>
            <div>
              <div className={`text-2xl font-bold ${team.budget_remaining < 0 ? 'text-destructive' : ''}`}>
                {team.budget_remaining.toFixed(1)}M
              </div>
              <div className="text-sm text-muted-foreground">Remaining</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Drivers */}
      <Card>
        <CardHeader>
          <CardTitle>Drivers ({team.drivers.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {team.drivers.map((driver) => (
              <div
                key={driver.driver_id}
                className="flex items-center justify-between p-3 rounded-lg border"
              >
                <div className="flex items-center gap-3">
                  {driver.driver_id === team.drs_boost_driver_id && (
                    <Zap className="h-4 w-4 text-yellow-500" />
                  )}
                  <div>
                    <div className="font-medium">{driver.driver_name}</div>
                    <div className="text-sm text-muted-foreground">{driver.team_name}</div>
                  </div>
                </div>
                <div className="font-bold">{driver.price.toFixed(1)}M</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Constructors */}
      <Card>
        <CardHeader>
          <CardTitle>Constructors ({team.constructors.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {team.constructors.map((constructor) => (
              <div
                key={constructor.constructor_id}
                className="flex items-center justify-between p-3 rounded-lg border"
              >
                <div className="font-medium">{constructor.constructor_name}</div>
                <div className="font-bold">{constructor.price.toFixed(1)}M</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Validation Errors */}
      {!team.is_valid && team.validation_errors.length > 0 && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Validation Errors</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-1">
              {team.validation_errors.map((error, index) => (
                <li key={index}>{error.message}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
```

### Step 2: Create TransferHistory Component

**File:** `src/components/teams/TransferHistory.tsx`

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TransferRecord } from '@/types/team'

interface TransferHistoryProps {
  transfers: TransferRecord[]
}

export const TransferHistory = ({ transfers }: TransferHistoryProps) => {
  if (transfers.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Transfer History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No transfers yet</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Transfer History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {transfers.map((transfer, index) => (
            <div key={index} className="p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm text-muted-foreground">
                  {new Date(transfer.timestamp).toLocaleDateString()}
                </div>
                {transfer.penalty_points > 0 && (
                  <Badge variant="destructive">
                    -{transfer.penalty_points} points
                  </Badge>
                )}
              </div>
              <div className="text-sm">
                <span className="font-medium">Transfers:</span> {transfer.transfers_used} / {transfer.transfers_available}
              </div>
              {transfer.changes.length > 0 && (
                <div className="mt-2 space-y-1">
                  {transfer.changes.map((change, idx) => (
                    <div key={idx} className="text-sm text-muted-foreground">
                      • {JSON.stringify(change)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
```

### Step 3: Create TeamDetail Page

**File:** `src/pages/TeamDetail.tsx`

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
import { ArrowLeft, Edit } from 'lucide-react'

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

  if (loading) {
    return <LoadingSpinner size="lg" className="mt-12" />
  }

  if (error || !team) {
    return <ErrorDisplay message={error || 'Team not found'} />
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div className="flex-1" />
        <Button asChild>
          <Link to={`/teams/${id}/edit`}>
            <Edit className="h-4 w-4 mr-2" />
            Edit Team
          </Link>
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TeamDetailView team={team} />
        </div>
        <div>
          <TransferHistory transfers={team.transfer_history} />
        </div>
      </div>
    </div>
  )
}
```

### Step 4: Create TeamEdit Page

**File:** `src/pages/TeamEdit.tsx`

```typescript
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
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
import { AlertCircle } from 'lucide-react'

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
  const transferCount = () => {
    const currentDriverIds = selectedDrivers.map(d => d.driver_id)
    const currentConstructorIds = selectedConstructors.map(c => c.constructor_id)

    const driversAdded = currentDriverIds.filter(id => !originalDriverIds.includes(id)).length
    const driversRemoved = originalDriverIds.filter(id => !currentDriverIds.includes(id)).length
    const constructorsAdded = currentConstructorIds.filter(id => !originalConstructorIds.includes(id)).length
    const constructorsRemoved = originalConstructorIds.filter(id => !currentConstructorIds.includes(id)).length

    return driversAdded + driversRemoved + constructorsAdded + constructorsRemoved
  }

  const transfers = transferCount()
  const freeTransfers = 2
  const penaltyPoints = Math.max(0, (transfers - freeTransfers) * -10)

  // Load team data
  useEffect(() => {
    const fetchTeam = async () => {
      if (!id) return

      try {
        const data = await teamsApi.getById(id)
        setTeam(data)

        // Set original IDs for transfer tracking
        const driverIds = data.drivers.map(d => d.driver_id)
        const constructorIds = data.constructors.map(c => c.constructor_id)
        setOriginalDriverIds(driverIds)
        setOriginalConstructorIds(constructorIds)

        setDrsBoostDriverId(data.drs_boost_driver_id)
      } catch (err: any) {
        toast({
          title: 'Error',
          description: 'Failed to load team',
          variant: 'destructive',
        })
      }
    }

    fetchTeam()
  }, [id, toast])

  // Pre-populate selections when drivers/constructors load
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
        title: 'Validation Failed',
        description: 'Please fix the errors before submitting',
        variant: 'destructive',
      })
      return
    }

    try {
      setSubmitting(true)
      await teamsApi.update(id, {
        driver_ids: selectedDrivers.map((d) => d.driver_id),
        constructor_ids: selectedConstructors.map((c) => c.constructor_id),
        drs_boost_driver_id: drsBoostDriverId!,
      })

      toast({
        title: 'Success!',
        description: `Team updated${penaltyPoints > 0 ? ` (${penaltyPoints} point penalty)` : ''}`,
      })

      navigate(`/teams/${id}`)
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err.response?.data?.detail || 'Failed to update team',
        variant: 'destructive',
      })
    } finally {
      setSubmitting(false)
    }
  }

  if (!team || driversLoading || constructorsLoading) {
    return <LoadingSpinner size="lg" className="mt-12" />
  }

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Edit Team: {team.team_name}</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Transfer Warning */}
        {transfers > freeTransfers && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Transfer Penalty</AlertTitle>
            <AlertDescription>
              You have made {transfers} transfers. You will receive a {penaltyPoints} point penalty
              ({transfers - freeTransfers} excess transfers × -10 points each).
            </AlertDescription>
          </Alert>
        )}

        {transfers > 0 && transfers <= freeTransfers && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Transfers</AlertTitle>
            <AlertDescription>
              You have made {transfers} of {freeTransfers} free transfers.
            </AlertDescription>
          </Alert>
        )}

        <ValidationErrors errors={errors} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="space-y-6">
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

          <div>
            <DriverSelector
              drivers={drivers}
              selectedDrivers={selectedDrivers}
              onSelectionChange={setSelectedDrivers}
              maxSelection={5}
            />
          </div>

          <div>
            <ConstructorSelector
              constructors={constructors}
              selectedConstructors={selectedConstructors}
              onSelectionChange={setSelectedConstructors}
              maxSelection={2}
            />
          </div>
        </div>

        <div className="flex gap-4">
          <Button
            type="submit"
            disabled={!isValid || submitting}
            className="flex-1"
          >
            {submitting ? <LoadingSpinner size="sm" /> : 'Update Team'}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate(`/teams/${id}`)}
            disabled={submitting}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}
```

---

## Testing Requirements

### Unit Tests

**Test TeamDetailView Component:**

Create `src/components/teams/__tests__/TeamDetailView.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { TeamDetailView } from '../TeamDetailView'
import { FantasyTeam } from '@/types/team'

const mockTeam: FantasyTeam = {
  team_id: '123',
  team_name: 'Test Team',
  created_by: 'user123',
  season: 2026,
  drivers: [
    {
      driver_id: 'd1',
      driver_name: 'Max Verstappen',
      team_name: 'Red Bull',
      price: 30.0,
    },
  ],
  constructors: [
    {
      constructor_id: 'c1',
      constructor_name: 'Red Bull',
      price: 25.0,
    },
  ],
  drs_boost_driver_id: 'd1',
  budget_cap: 100.0,
  budget_used: 55.0,
  budget_remaining: 45.0,
  is_valid: true,
  validation_errors: [],
  transfer_history: [],
  current_race_transfers: 0,
  available_transfers: 2,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

describe('TeamDetailView', () => {
  it('renders team name and season', () => {
    render(<TeamDetailView team={mockTeam} />)

    expect(screen.getByText('Test Team')).toBeInTheDocument()
    expect(screen.getByText('Season 2026')).toBeInTheDocument()
  })

  it('displays budget information', () => {
    render(<TeamDetailView team={mockTeam} />)

    expect(screen.getByText('100.0M')).toBeInTheDocument()
    expect(screen.getByText('55.0M')).toBeInTheDocument()
    expect(screen.getByText('45.0M')).toBeInTheDocument()
  })

  it('shows DRS boost indicator', () => {
    render(<TeamDetailView team={mockTeam} />)

    // Check for lightning bolt icon (Zap) near driver with DRS boost
    const drsBoostElements = screen.getAllByText('Max Verstappen')
    expect(drsBoostElements.length).toBeGreaterThan(0)
  })

  it('displays validation errors for invalid team', () => {
    const invalidTeam = {
      ...mockTeam,
      is_valid: false,
      validation_errors: [
        { rule_type: 'budget_cap', severity: 'error' as const, message: 'Team exceeds budget' },
      ],
    }

    render(<TeamDetailView team={invalidTeam} />)

    expect(screen.getByText('Validation Errors')).toBeInTheDocument()
    expect(screen.getByText('Team exceeds budget')).toBeInTheDocument()
  })
})
```

---

## Manual Testing Checklist

### Team Detail Page
- [ ] Team name and season display correctly
- [ ] Budget summary shows cap/used/remaining
- [ ] All drivers display with correct info
- [ ] DRS boost indicator (⚡) shows on correct driver
- [ ] All constructors display with correct info
- [ ] Valid badge shows green for valid team
- [ ] Invalid badge shows red for invalid team
- [ ] Validation errors display (if team invalid)
- [ ] Transfer history displays (if transfers made)
- [ ] "Edit Team" button navigates to edit page
- [ ] "Back" button returns to dashboard

### Team Edit Page
- [ ] Form pre-populates with existing team data
- [ ] Can change driver selections
- [ ] Can change constructor selections
- [ ] Can change DRS boost assignment
- [ ] Budget updates in real-time
- [ ] Transfer count calculates correctly
- [ ] "Free transfers" message shows when ≤ 2 transfers
- [ ] Penalty warning shows when > 2 transfers
- [ ] Penalty calculation is correct (excess × -10)
- [ ] Cannot submit if validation fails
- [ ] Submit shows loading spinner
- [ ] Success redirects to detail page
- [ ] Success toast shows penalty if applicable
- [ ] Cancel button returns to detail page

### Transfer Tracking
- [ ] Adding 1 driver = 1 transfer
- [ ] Removing 1 driver = 1 transfer
- [ ] Swapping 1 driver = 2 transfers
- [ ] Adding 1 constructor = 1 transfer
- [ ] Making 3 changes = 3 transfers = -10 points penalty
- [ ] Making 5 changes = 5 transfers = -30 points penalty
- [ ] Changing only DRS boost = 0 transfers

---

## Acceptance Criteria

✅ **Feature is complete when:**

1. Team detail page displays all information correctly
2. Transfer history displays properly
3. Edit page pre-populates with existing data
4. Transfer count calculates correctly
5. Penalty calculation is accurate
6. Transfer warnings display appropriately
7. Form validation works on edit page
8. Team updates successfully via API
9. All unit tests pass
10. All manual tests pass
11. No TypeScript errors
12. No console errors or warnings

---

## Iteration Instructions

**Keep iterating until all tests pass:**

1. **Build incrementally:**
   - TeamDetailView → test
   - TransferHistory → test
   - TeamDetail page → test end-to-end
   - TeamEdit page → test end-to-end
   - Transfer calculation → verify accuracy

2. **Test transfer logic thoroughly:**
   - Make 1 change → verify count = 1
   - Make 2 changes → verify count = 2, no penalty
   - Make 3 changes → verify count = 3, penalty = -10
   - Make 5 changes → verify count = 5, penalty = -30
   - Reset selections → verify count resets

3. **Verify with backend:**
   - Check that transfer_history updates after edit
   - Verify penalty is recorded correctly
   - Confirm validation still runs on edit

4. **Common Issues:**
   - Pre-population not working → check useEffect dependencies
   - Transfer count wrong → verify original IDs are set correctly
   - Penalty not showing → check calculation logic
   - Edit fails → verify API endpoint and request body

5. **Repeat** until all acceptance criteria met

---

## Definition of Done

- [ ] All components implemented
- [ ] All unit tests passing
- [ ] All manual tests passing
- [ ] Transfer tracking accurate
- [ ] Penalty calculation correct
- [ ] Pre-population working
- [ ] Edit submits successfully
- [ ] No TypeScript errors
- [ ] No linting errors
- [ ] Responsive layout verified
- [ ] Code committed with clear message

**Proceed to Rules Admin feature once complete.**
