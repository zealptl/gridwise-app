# Feature: Team Creation Form

## Overview

Build the complete team creation experience with real-time validation, budget tracking, and player selection.

**Estimated Time:** 4-5 hours
**Dependencies:** Foundation setup + Dashboard feature
**Complexity:** High (Most Complex Feature)

---

## Feature Requirements

### Functional Requirements
- Multi-select driver picker (exactly 5 drivers)
- Multi-select constructor picker (exactly 2 constructors)
- Search and filter drivers by name and team
- Real-time budget calculation (100M cap)
- DRS Boost assignment (one driver)
- Client-side validation with error messages
- Submit button disabled until valid
- API integration with backend validation
- Redirect to team detail page on success
- Error handling for API failures

### Business Rules
- Exactly 5 drivers required
- Exactly 2 constructors required
- Total cost must not exceed 100M budget
- DRS Boost must be assigned to one of the selected drivers
- Only active drivers and constructors can be selected

---

## Implementation Steps

### Step 1: Create BudgetDisplay Component

**File:** `src/components/teams/BudgetDisplay.tsx`

```typescript
import { Progress } from '@/components/ui/progress'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface BudgetDisplayProps {
  budgetUsed: number
  budgetRemaining: number
  budgetCap: number
  isOverBudget: boolean
}

export const BudgetDisplay = ({
  budgetUsed,
  budgetRemaining,
  budgetCap,
  isOverBudget,
}: BudgetDisplayProps) => {
  const percentage = (budgetUsed / budgetCap) * 100

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Budget</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex justify-between text-sm">
            <span>Used: <span className="font-bold">{budgetUsed.toFixed(1)}M</span></span>
            <span className={isOverBudget ? 'text-destructive font-bold' : 'text-muted-foreground'}>
              Remaining: {budgetRemaining.toFixed(1)}M
            </span>
          </div>

          <Progress
            value={percentage}
            className={isOverBudget ? 'bg-destructive' : ''}
          />

          <div className="text-xs text-muted-foreground text-center">
            Budget Cap: {budgetCap.toFixed(1)}M
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
```

### Step 2: Create DriverSelector Component

**File:** `src/components/teams/DriverSelector.tsx`

```typescript
import { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Driver } from '@/types/driver'
import { Search } from 'lucide-react'

interface DriverSelectorProps {
  drivers: Driver[]
  selectedDrivers: Driver[]
  onSelectionChange: (drivers: Driver[]) => void
  maxSelection?: number
}

export const DriverSelector = ({
  drivers,
  selectedDrivers,
  onSelectionChange,
  maxSelection = 5,
}: DriverSelectorProps) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [teamFilter, setTeamFilter] = useState<string | null>(null)

  const filteredDrivers = useMemo(() => {
    return drivers.filter((driver) => {
      const matchesSearch =
        driver.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        driver.last_name.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesTeam = !teamFilter || driver.team_name === teamFilter
      return matchesSearch && matchesTeam && driver.status === 'active'
    })
  }, [drivers, searchTerm, teamFilter])

  const teams = useMemo(() => {
    return Array.from(new Set(drivers.map((d) => d.team_name)))
  }, [drivers])

  const handleToggle = (driver: Driver) => {
    const isSelected = selectedDrivers.some((d) => d.driver_id === driver.driver_id)

    if (isSelected) {
      onSelectionChange(selectedDrivers.filter((d) => d.driver_id !== driver.driver_id))
    } else if (selectedDrivers.length < maxSelection) {
      onSelectionChange([...selectedDrivers, driver])
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">
          Select Drivers ({selectedDrivers.length}/{maxSelection})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search drivers..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>

          {/* Team Filter */}
          <div className="flex flex-wrap gap-2">
            <Badge
              variant={teamFilter === null ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setTeamFilter(null)}
            >
              All Teams
            </Badge>
            {teams.map((team) => (
              <Badge
                key={team}
                variant={teamFilter === team ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => setTeamFilter(team)}
              >
                {team}
              </Badge>
            ))}
          </div>

          {/* Driver List */}
          <div className="max-h-96 overflow-y-auto space-y-2">
            {filteredDrivers.map((driver) => {
              const isSelected = selectedDrivers.some((d) => d.driver_id === driver.driver_id)
              const canSelect = selectedDrivers.length < maxSelection || isSelected

              return (
                <div
                  key={driver.driver_id}
                  className={`flex items-center justify-between p-3 rounded-lg border ${
                    isSelected ? 'bg-primary/10 border-primary' : 'hover:bg-muted'
                  } ${!canSelect ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                  onClick={() => canSelect && handleToggle(driver)}
                >
                  <div className="flex items-center gap-3">
                    <Checkbox checked={isSelected} disabled={!canSelect} />
                    <div>
                      <div className="font-medium">
                        {driver.first_name} {driver.last_name}
                      </div>
                      <div className="text-sm text-muted-foreground">{driver.team_name}</div>
                    </div>
                  </div>
                  <div className="font-bold">{driver.price.toFixed(1)}M</div>
                </div>
              )
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
```

### Step 3: Create ConstructorSelector Component

**File:** `src/components/teams/ConstructorSelector.tsx`

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Constructor } from '@/types/constructor'

interface ConstructorSelectorProps {
  constructors: Constructor[]
  selectedConstructors: Constructor[]
  onSelectionChange: (constructors: Constructor[]) => void
  maxSelection?: number
}

export const ConstructorSelector = ({
  constructors,
  selectedConstructors,
  onSelectionChange,
  maxSelection = 2,
}: ConstructorSelectorProps) => {
  const handleToggle = (constructor: Constructor) => {
    const isSelected = selectedConstructors.some((c) => c.constructor_id === constructor.constructor_id)

    if (isSelected) {
      onSelectionChange(selectedConstructors.filter((c) => c.constructor_id !== constructor.constructor_id))
    } else if (selectedConstructors.length < maxSelection) {
      onSelectionChange([...selectedConstructors, constructor])
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">
          Select Constructors ({selectedConstructors.length}/{maxSelection})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {constructors
            .filter((c) => c.status === 'active')
            .map((constructor) => {
              const isSelected = selectedConstructors.some((c) => c.constructor_id === constructor.constructor_id)
              const canSelect = selectedConstructors.length < maxSelection || isSelected

              return (
                <div
                  key={constructor.constructor_id}
                  className={`flex items-center justify-between p-3 rounded-lg border ${
                    isSelected ? 'bg-primary/10 border-primary' : 'hover:bg-muted'
                  } ${!canSelect ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                  onClick={() => canSelect && handleToggle(constructor)}
                >
                  <div className="flex items-center gap-3">
                    <Checkbox checked={isSelected} disabled={!canSelect} />
                    <div>
                      <div className="font-medium">{constructor.name}</div>
                      <div className="text-sm text-muted-foreground">{constructor.full_name}</div>
                    </div>
                  </div>
                  <div className="font-bold">{constructor.price.toFixed(1)}M</div>
                </div>
              )
            })}
        </div>
      </CardContent>
    </Card>
  )
}
```

### Step 4: Create DrsBoostSelector Component

**File:** `src/components/teams/DrsBoostSelector.tsx`

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import { Driver } from '@/types/driver'

interface DrsBoostSelectorProps {
  selectedDrivers: Driver[]
  drsBoostDriverId: string | null
  onDrsBoostChange: (driverId: string) => void
}

export const DrsBoostSelector = ({
  selectedDrivers,
  drsBoostDriverId,
  onDrsBoostChange,
}: DrsBoostSelectorProps) => {
  if (selectedDrivers.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">DRS Boost</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Select drivers first to assign DRS Boost
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">DRS Boost</CardTitle>
      </CardHeader>
      <CardContent>
        <RadioGroup value={drsBoostDriverId || ''} onValueChange={onDrsBoostChange}>
          <div className="space-y-2">
            {selectedDrivers.map((driver) => (
              <div key={driver.driver_id} className="flex items-center space-x-2">
                <RadioGroupItem value={driver.driver_id} id={driver.driver_id} />
                <Label htmlFor={driver.driver_id} className="cursor-pointer">
                  {driver.first_name} {driver.last_name}
                </Label>
              </div>
            ))}
          </div>
        </RadioGroup>
      </CardContent>
    </Card>
  )
}
```

### Step 5: Create ValidationErrors Component

**File:** `src/components/teams/ValidationErrors.tsx`

```typescript
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'

interface ValidationErrorsProps {
  errors: string[]
}

export const ValidationErrors = ({ errors }: ValidationErrorsProps) => {
  if (errors.length === 0) return null

  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Team Validation Failed</AlertTitle>
      <AlertDescription>
        <ul className="list-disc list-inside mt-2 space-y-1">
          {errors.map((error, index) => (
            <li key={index}>{error}</li>
          ))}
        </ul>
      </AlertDescription>
    </Alert>
  )
}
```

### Step 6: Update TeamCreate Page

**File:** `src/pages/TeamCreate.tsx`

```typescript
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
        title: 'Error',
        description: 'Please enter a team name',
        variant: 'destructive',
      })
      return
    }

    if (!isValid) {
      toast({
        title: 'Validation Failed',
        description: 'Please fix the errors before submitting',
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
        title: 'Success!',
        description: 'Team created successfully',
      })

      navigate(`/teams/${team.team_id}`)
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err.response?.data?.detail || 'Failed to create team',
        variant: 'destructive',
      })
    } finally {
      setSubmitting(false)
    }
  }

  if (driversLoading || constructorsLoading) {
    return <LoadingSpinner size="lg" className="mt-12" />
  }

  if (driversError) {
    return <ErrorDisplay message={driversError} />
  }

  if (constructorsError) {
    return <ErrorDisplay message={constructorsError} />
  }

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Create New Team</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Team Name */}
        <div className="space-y-2">
          <Label htmlFor="team-name">Team Name</Label>
          <Input
            id="team-name"
            value={teamName}
            onChange={(e) => setTeamName(e.target.value)}
            placeholder="Enter team name"
            required
          />
        </div>

        {/* Validation Errors */}
        <ValidationErrors errors={errors} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Budget & DRS */}
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

          {/* Middle Column - Drivers */}
          <div>
            <DriverSelector
              drivers={drivers}
              selectedDrivers={selectedDrivers}
              onSelectionChange={setSelectedDrivers}
              maxSelection={5}
            />
          </div>

          {/* Right Column - Constructors */}
          <div>
            <ConstructorSelector
              constructors={constructors}
              selectedConstructors={selectedConstructors}
              onSelectionChange={setSelectedConstructors}
              maxSelection={2}
            />
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex gap-4">
          <Button
            type="submit"
            disabled={!isValid || submitting}
            className="flex-1"
          >
            {submitting ? <LoadingSpinner size="sm" /> : 'Create Team'}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/')}
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

**Test Budget Calculator Hook:**

Create `src/hooks/__tests__/useBudgetCalculator.test.tsx`:

```typescript
import { renderHook } from '@testing-library/react'
import { useBudgetCalculator } from '../useBudgetCalculator'
import { Driver } from '@/types/driver'
import { Constructor } from '@/types/constructor'

describe('useBudgetCalculator', () => {
  const mockDrivers: Driver[] = [
    { driver_id: '1', price: 10.5 } as Driver,
    { driver_id: '2', price: 15.0 } as Driver,
  ]

  const mockConstructors: Constructor[] = [
    { constructor_id: '1', price: 20.0 } as Constructor,
  ]

  it('calculates budget correctly', () => {
    const { result } = renderHook(() =>
      useBudgetCalculator({
        selectedDrivers: mockDrivers,
        selectedConstructors: mockConstructors,
        budgetCap: 100.0,
      })
    )

    expect(result.current.budgetUsed).toBe(45.5)
    expect(result.current.budgetRemaining).toBe(54.5)
    expect(result.current.isOverBudget).toBe(false)
  })

  it('detects over budget', () => {
    const expensiveDrivers: Driver[] = [
      { driver_id: '1', price: 50.0 } as Driver,
      { driver_id: '2', price: 30.0 } as Driver,
    ]

    const expensiveConstructors: Constructor[] = [
      { constructor_id: '1', price: 25.0 } as Constructor,
    ]

    const { result } = renderHook(() =>
      useBudgetCalculator({
        selectedDrivers: expensiveDrivers,
        selectedConstructors: expensiveConstructors,
        budgetCap: 100.0,
      })
    )

    expect(result.current.budgetUsed).toBe(105.0)
    expect(result.current.budgetRemaining).toBe(-5.0)
    expect(result.current.isOverBudget).toBe(true)
  })
})
```

**Test Team Validation Hook:**

Create `src/hooks/__tests__/useTeamValidation.test.tsx`:

```typescript
import { renderHook } from '@testing-library/react'
import { useTeamValidation } from '../useTeamValidation'
import { Driver } from '@/types/driver'
import { Constructor } from '@/types/constructor'

describe('useTeamValidation', () => {
  it('validates correct team as valid', () => {
    const drivers: Driver[] = new Array(5).fill({ driver_id: 'test' } as Driver)
    const constructors: Constructor[] = new Array(2).fill({ constructor_id: 'test' } as Constructor)

    const { result } = renderHook(() =>
      useTeamValidation({
        selectedDrivers: drivers,
        selectedConstructors: constructors,
        drsBoostDriverId: 'test',
        budgetRemaining: 10.0,
      })
    )

    expect(result.current.isValid).toBe(true)
    expect(result.current.errors).toHaveLength(0)
  })

  it('catches incorrect driver count', () => {
    const { result } = renderHook(() =>
      useTeamValidation({
        selectedDrivers: [],
        selectedConstructors: new Array(2).fill({ constructor_id: 'test' } as Constructor),
        drsBoostDriverId: null,
        budgetRemaining: 10.0,
      })
    )

    expect(result.current.isValid).toBe(false)
    expect(result.current.errors).toContain('You must select exactly 5 drivers')
  })

  it('catches budget exceeded', () => {
    const drivers: Driver[] = new Array(5).fill({ driver_id: 'test' } as Driver)
    const constructors: Constructor[] = new Array(2).fill({ constructor_id: 'test' } as Constructor)

    const { result } = renderHook(() =>
      useTeamValidation({
        selectedDrivers: drivers,
        selectedConstructors: constructors,
        drsBoostDriverId: 'test',
        budgetRemaining: -5.0,
      })
    )

    expect(result.current.isValid).toBe(false)
    expect(result.current.errors).toContain('Team exceeds budget cap')
  })
})
```

---

## Manual Testing Checklist

### Form Functionality
- [ ] Team name input works
- [ ] Search bar filters drivers by name
- [ ] Team filter buttons filter drivers by F1 team
- [ ] Can select up to 5 drivers
- [ ] Cannot select more than 5 drivers
- [ ] Can deselect drivers
- [ ] Can select up to 2 constructors
- [ ] Cannot select more than 2 constructors
- [ ] Can deselect constructors

### Budget Calculation
- [ ] Budget updates in real-time when selecting/deselecting
- [ ] Budget Used displays correct total
- [ ] Budget Remaining displays correct amount
- [ ] Progress bar fills proportionally
- [ ] Over-budget shows red warning

### DRS Boost
- [ ] DRS Boost section hidden when no drivers selected
- [ ] DRS Boost shows all selected drivers
- [ ] Can select one driver for DRS Boost
- [ ] Radio button works correctly

### Validation
- [ ] Validation errors display when requirements not met
- [ ] "You must select exactly 5 drivers" shows when < 5 drivers
- [ ] "You must select exactly 2 constructors" shows when ≠ 2 constructors
- [ ] "Team exceeds budget cap" shows when over budget
- [ ] "You must assign DRS Boost" shows when not assigned
- [ ] Submit button disabled when validation fails
- [ ] Submit button enabled when all valid

### Form Submission
- [ ] Cannot submit without team name
- [ ] Cannot submit with validation errors
- [ ] Submit shows loading spinner
- [ ] Success creates team and redirects to detail page
- [ ] Error shows toast notification
- [ ] Cancel button returns to dashboard

### Responsiveness
- [ ] Layout works on mobile (stacked columns)
- [ ] Layout works on tablet (2 columns)
- [ ] Layout works on desktop (3 columns)
- [ ] Scrolling works in driver/constructor lists

---

## Acceptance Criteria

✅ **Feature is complete when:**

1. All player selection components work correctly
2. Real-time budget calculation is accurate
3. Validation prevents invalid team creation
4. Form submits successfully to backend
5. Redirects to team detail page on success
6. All unit tests pass
7. All manual tests pass
8. Responsive layout works on all screen sizes
9. No TypeScript errors
10. No console errors or warnings

---

## Iteration Instructions

**Keep iterating until all tests pass:**

1. **Build incrementally:**
   - Start with BudgetDisplay → test
   - Add DriverSelector → test
   - Add ConstructorSelector → test
   - Add DrsBoostSelector → test
   - Add ValidationErrors → test
   - Integrate in TeamCreate page → test end-to-end

2. **Run tests after each component:** `npm run test`

3. **Test manually after each component:**
   - Load page in browser
   - Interact with new component
   - Check console for errors
   - Verify state updates correctly

4. **Debug issues:**
   - Read error messages carefully
   - Use browser DevTools React extension
   - Log state changes to console
   - Verify API responses in Network tab

5. **Repeat** until all acceptance criteria met

### Common Issues & Solutions

**Issue:** Budget not updating
- **Solution:** Check `useMemo` dependencies in `useBudgetCalculator`
- **Solution:** Verify selectedDrivers/selectedConstructors are updating

**Issue:** Can't select drivers
- **Solution:** Verify `handleToggle` function logic
- **Solution:** Check `canSelect` calculation
- **Solution:** Ensure drivers have `driver_id` field

**Issue:** DRS Boost not working
- **Solution:** Check RadioGroup `value` and `onValueChange` props
- **Solution:** Verify driver IDs match between selection and radio options

**Issue:** Form submission fails
- **Solution:** Check API endpoint is correct (`/api/v1/teams`)
- **Solution:** Verify request body matches backend schema
- **Solution:** Check browser Network tab for error details

**Issue:** Validation not working
- **Solution:** Verify `useTeamValidation` is called with correct props
- **Solution:** Check validation logic in hook
- **Solution:** Ensure errors array is passed to ValidationErrors component

---

## Definition of Done

- [ ] All components implemented and working
- [ ] All unit tests written and passing
- [ ] All manual tests passing
- [ ] Real-time updates working correctly
- [ ] Form submits to backend successfully
- [ ] Redirects to detail page on success
- [ ] Error handling working for all failure cases
- [ ] No TypeScript errors
- [ ] No linting errors
- [ ] Responsive on mobile/tablet/desktop
- [ ] Browser console clean
- [ ] Code committed with clear message

**This is the most complex feature - take time to test thoroughly before moving on.**
