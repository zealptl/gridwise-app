# Feature: Team Creation Form (Design-Refined)

## Overview

Build the complete team creation experience with real-time validation, budget tracking, and player selection.

**Estimated Time:** 4-5 hours
**Dependencies:** Foundation setup + Dashboard feature
**Complexity:** High (Most Complex Feature)

---

## Design Philosophy

This is the most complex screen in the app. Complexity is the enemy. The goal: make selecting 5 drivers, 2 constructors, and 1 DRS boost feel like a guided conversation, not a form to fill out. Progressive disclosure. Clear hierarchy. Real-time feedback. The user should never wonder "what next?"

### Design Principles Applied
- **Progressive Disclosure:** Don't show everything at once. Reveal as needed.
- **Real-Time Feedback:** Budget and validation update instantly, never lag
- **Error Prevention:** Disable invalid options before the user clicks them
- **Visual Hierarchy:** Current selection status always visible, clearly separated from picker
- **Mobile First:** Vertical stack on mobile, side-by-side on desktop
- **Guided Flow:** User knows exactly what step they're on and what's remaining

---

## Feature Requirements

### Functional Requirements
- Team name input (required, unique)
- Multi-select driver picker (exactly 5 drivers)
- Multi-select constructor picker (exactly 2 constructors)
- Search and filter drivers by name and team
- Real-time budget calculation (100M cap)
- DRS Boost assignment (one driver from selected 5)
- Client-side validation with real-time error messages
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

### Design Requirements
- **Form never feels overwhelming** - one section at a time gets focus
- **Budget is always visible** - sticky sidebar on desktop, persistent top section on mobile
- **Selection count is clear** - "3 of 5 drivers selected" always visible
- **Real-time validation is gentle** - show progress, not just errors
- **Empty states guide next action** - "Select drivers to assign DRS Boost"
- **Disabled states are obvious** - can't select 6th driver, visual feedback explains why
- **Touch targets are generous** - minimum 44px on mobile
- **Animations are purposeful** - budget bar fills, errors fade in, nothing jumps

---

## Design System Tokens Required

Add these to `DESIGN_SYSTEM.md`:

```yaml
# Form Specific Spacing
form-section-gap: 32px       # Gap between major form sections
form-input-gap: 12px         # Gap between label and input
form-field-gap: 20px         # Gap between form fields

# Selection States
selected-bg: hsl(var(--primary) / 0.1)
selected-border: hsl(var(--primary))
disabled-opacity: 0.5
hover-lift: -2px

# Budget Visualization
budget-safe: hsl(142, 76%, 36%)      # Under budget (green)
budget-warning: hsl(38, 92%, 50%)    # Near budget (amber)
budget-danger: hsl(0, 84%, 60%)      # Over budget (red)

# Animations
slide-in: 300ms cubic-bezier(0.16, 1, 0.3, 1)
fade-in: 200ms ease-out
scale-in: 150ms cubic-bezier(0.16, 1, 0.3, 1)

# Sticky Positioning
sticky-top-mobile: 72px    # Below mobile header
sticky-top-desktop: 24px   # Desktop sticky offset
```

---

## Progressive Flow Design

**Step 1:** Name your team (immediate focus)
**Step 2:** Budget overview appears (establishes constraints)
**Step 3:** Select 5 drivers (primary action, most important)
**Step 4:** Select 2 constructors (secondary, supports drivers)
**Step 5:** Assign DRS Boost (final detail, only after drivers selected)
**Step 6:** Review & Submit (validation summary, clear CTA)

At each step, the user sees:
- What they've completed ✓
- What they're working on (highlighted)
- What's next (subtle, not distracting)

---

## Implementation Steps

### Step 1: Enhanced BudgetDisplay Component

**File:** `src/components/teams/BudgetDisplay.tsx`

**Design Notes:**
- Sticky on desktop, persistent on mobile
- Progress bar uses semantic colors (green safe, amber warning, red danger)
- Numbers are large and clear
- State transitions smoothly (color changes animate)

```typescript
import { useMemo } from 'react'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle, CheckCircle } from 'lucide-react'

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

  // Semantic color based on budget status
  const statusColor = useMemo(() => {
    if (isOverBudget) return 'text-red-600'
    if (percentage > 90) return 'text-amber-600'
    return 'text-green-600'
  }, [isOverBudget, percentage])

  const progressColor = useMemo(() => {
    if (isOverBudget) return 'bg-red-600'
    if (percentage > 90) return 'bg-amber-600'
    return 'bg-green-600'
  }, [isOverBudget, percentage])

  return (
    <Card className="sticky top-6">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          Budget
          {isOverBudget ? (
            <AlertCircle className="h-4 w-4 text-red-600" aria-label="Over budget" />
          ) : percentage === 100 ? (
            <CheckCircle className="h-4 w-4 text-green-600" aria-label="Budget maximized" />
          ) : null}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Large Number Display - Primary Hierarchy */}
        <div className="space-y-1">
          <div className="flex items-baseline justify-between">
            <span className="text-sm text-muted-foreground">Used</span>
            <span className={`text-2xl font-bold tabular-nums ${statusColor} transition-colors duration-200`}>
              {budgetUsed.toFixed(1)}M
            </span>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-sm text-muted-foreground">Remaining</span>
            <span className={`text-lg font-semibold tabular-nums ${isOverBudget ? 'text-red-600' : 'text-muted-foreground'} transition-colors duration-200`}>
              {budgetRemaining.toFixed(1)}M
            </span>
          </div>
        </div>

        {/* Visual Progress - Animated */}
        <div className="space-y-2">
          <Progress
            value={Math.min(percentage, 100)}
            className="h-3 transition-all duration-300"
            indicatorClassName={`${progressColor} transition-colors duration-300`}
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>0M</span>
            <span>{budgetCap}M</span>
          </div>
        </div>

        {/* Status Message - Contextual */}
        {isOverBudget && (
          <div className="text-sm text-red-600 font-medium bg-red-50 rounded-md px-3 py-2 animate-in fade-in slide-in-from-top-2 duration-200">
            Over budget by {Math.abs(budgetRemaining).toFixed(1)}M
          </div>
        )}

        {!isOverBudget && percentage > 95 && (
          <div className="text-sm text-amber-700 font-medium bg-amber-50 rounded-md px-3 py-2">
            Almost at budget cap
          </div>
        )}

        {!isOverBudget && budgetUsed === 0 && (
          <div className="text-sm text-muted-foreground bg-muted rounded-md px-3 py-2">
            Select players to see budget usage
          </div>
        )}
      </CardContent>
    </Card>
  )
}
```

### Step 2: Enhanced DriverSelector Component

**File:** `src/components/teams/DriverSelector.tsx`

**Design Notes:**
- Selection count always visible in header
- Search has focus indicator and clear button
- Team filter pills are touch-friendly (minimum 36px height)
- Selected drivers have distinct visual state (border, background, checkmark)
- Disabled drivers fade out with tooltip explaining why
- List is scrollable with subtle shadow at top when scrolled

```typescript
import { useState, useMemo, useRef, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Driver } from '@/types/driver'
import { Search, X, Users } from 'lucide-react'

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
  const searchInputRef = useRef<HTMLInputElement>(null)

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
    return Array.from(new Set(drivers.map((d) => d.team_name).filter(Boolean))).sort()
  }, [drivers])

  const handleToggle = (driver: Driver) => {
    const isSelected = selectedDrivers.some((d) => d.driver_id === driver.driver_id)

    if (isSelected) {
      onSelectionChange(selectedDrivers.filter((d) => d.driver_id !== driver.driver_id))
    } else if (selectedDrivers.length < maxSelection) {
      onSelectionChange([...selectedDrivers, driver])
    }
  }

  const clearSearch = () => {
    setSearchTerm('')
    searchInputRef.current?.focus()
  }

  const selectionComplete = selectedDrivers.length === maxSelection

  return (
    <Card className={selectionComplete ? 'ring-2 ring-green-200' : ''}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Users className="h-5 w-5" aria-hidden="true" />
            Select Drivers
          </CardTitle>
          <Badge
            variant={selectionComplete ? 'default' : 'secondary'}
            className="text-base px-3 py-1"
          >
            {selectedDrivers.length} / {maxSelection}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Search Input - Focus First */}
        <div className="relative">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none"
            aria-hidden="true"
          />
          <Input
            ref={searchInputRef}
            placeholder="Search by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9 pr-9"
            aria-label="Search drivers"
          />
          {searchTerm && (
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
              onClick={clearSearch}
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Team Filter Pills - Touch Friendly */}
        <div className="flex flex-wrap gap-2">
          <Badge
            variant={teamFilter === null ? 'default' : 'outline'}
            className="cursor-pointer px-3 py-1.5 transition-colors"
            onClick={() => setTeamFilter(null)}
          >
            All Teams
          </Badge>
          {teams.map((team) => (
            <Badge
              key={team}
              variant={teamFilter === team ? 'default' : 'outline'}
              className="cursor-pointer px-3 py-1.5 transition-colors"
              onClick={() => setTeamFilter(team)}
            >
              {team}
            </Badge>
          ))}
        </div>

        {/* Driver List - Scrollable with Clear Selection States */}
        <ScrollArea className="h-[400px] -mr-4 pr-4">
          <div className="space-y-2">
            {filteredDrivers.length === 0 ? (
              <div className="text-center py-8 text-sm text-muted-foreground">
                No drivers found
              </div>
            ) : (
              filteredDrivers.map((driver) => {
                const isSelected = selectedDrivers.some((d) => d.driver_id === driver.driver_id)
                const canSelect = selectedDrivers.length < maxSelection || isSelected
                const isDisabled = !canSelect

                return (
                  <button
                    key={driver.driver_id}
                    type="button"
                    className={`
                      w-full flex items-center justify-between p-3 rounded-lg border-2 transition-all
                      ${isSelected
                        ? 'bg-primary/5 border-primary shadow-sm'
                        : 'border-border hover:bg-muted hover:border-muted-foreground/20'
                      }
                      ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
                    `}
                    onClick={() => canSelect && handleToggle(driver)}
                    disabled={isDisabled}
                    aria-pressed={isSelected}
                    aria-label={`${driver.first_name} ${driver.last_name}, ${driver.team_name}, ${driver.price}M${isSelected ? ', selected' : ''}${isDisabled ? ', cannot select more drivers' : ''}`}
                  >
                    <div className="flex items-center gap-3">
                      <Checkbox
                        checked={isSelected}
                        disabled={isDisabled}
                        aria-hidden="true"
                      />
                      <div className="text-left">
                        <div className="font-medium">
                          {driver.first_name} {driver.last_name}
                        </div>
                        <div className="text-sm text-muted-foreground">{driver.team_name}</div>
                      </div>
                    </div>
                    <div className="font-bold text-lg tabular-nums">{driver.price.toFixed(1)}M</div>
                  </button>
                )
              })
            )}
          </div>
        </ScrollArea>

        {/* Helper Text - Contextual */}
        {selectedDrivers.length === 0 && (
          <p className="text-sm text-muted-foreground text-center">
            Select {maxSelection} drivers to continue
          </p>
        )}
        {selectedDrivers.length > 0 && selectedDrivers.length < maxSelection && (
          <p className="text-sm text-muted-foreground text-center">
            Select {maxSelection - selectedDrivers.length} more {maxSelection - selectedDrivers.length === 1 ? 'driver' : 'drivers'}
          </p>
        )}
        {selectionComplete && (
          <p className="text-sm text-green-700 font-medium text-center bg-green-50 rounded-md px-3 py-2">
            Driver selection complete ✓
          </p>
        )}
      </CardContent>
    </Card>
  )
}
```

### Step 3: Enhanced ConstructorSelector Component

**File:** `src/components/teams/ConstructorSelector.tsx`

**Design Notes:**
- Similar visual language to DriverSelector for consistency
- Simpler UI (no search needed, smaller list)
- Clear selection count
- Same selection state patterns

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Constructor } from '@/types/constructor'
import { Building2 } from 'lucide-react'

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

  const selectionComplete = selectedConstructors.length === maxSelection

  return (
    <Card className={selectionComplete ? 'ring-2 ring-green-200' : ''}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Building2 className="h-5 w-5" aria-hidden="true" />
            Select Constructors
          </CardTitle>
          <Badge
            variant={selectionComplete ? 'default' : 'secondary'}
            className="text-base px-3 py-1"
          >
            {selectedConstructors.length} / {maxSelection}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-2">
          {constructors
            .filter((c) => c.status === 'active')
            .map((constructor) => {
              const isSelected = selectedConstructors.some((c) => c.constructor_id === constructor.constructor_id)
              const canSelect = selectedConstructors.length < maxSelection || isSelected
              const isDisabled = !canSelect

              return (
                <button
                  key={constructor.constructor_id}
                  type="button"
                  className={`
                    w-full flex items-center justify-between p-3 rounded-lg border-2 transition-all
                    ${isSelected
                      ? 'bg-primary/5 border-primary shadow-sm'
                      : 'border-border hover:bg-muted hover:border-muted-foreground/20'
                    }
                    ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
                  `}
                  onClick={() => canSelect && handleToggle(constructor)}
                  disabled={isDisabled}
                  aria-pressed={isSelected}
                  aria-label={`${constructor.name}, ${constructor.price}M${isSelected ? ', selected' : ''}${isDisabled ? ', cannot select more constructors' : ''}`}
                >
                  <div className="flex items-center gap-3">
                    <Checkbox
                      checked={isSelected}
                      disabled={isDisabled}
                      aria-hidden="true"
                    />
                    <div className="text-left">
                      <div className="font-medium">{constructor.name}</div>
                      <div className="text-sm text-muted-foreground">{constructor.full_name}</div>
                    </div>
                  </div>
                  <div className="font-bold text-lg tabular-nums">{constructor.price.toFixed(1)}M</div>
                </button>
              )
            })}
        </div>

        {/* Helper Text - Contextual */}
        <div className="mt-4">
          {selectedConstructors.length === 0 && (
            <p className="text-sm text-muted-foreground text-center">
              Select {maxSelection} constructors to continue
            </p>
          )}
          {selectedConstructors.length > 0 && selectedConstructors.length < maxSelection && (
            <p className="text-sm text-muted-foreground text-center">
              Select {maxSelection - selectedConstructors.length} more constructor{maxSelection - selectedConstructors.length !== 1 ? 's' : ''}
            </p>
          )}
          {selectionComplete && (
            <p className="text-sm text-green-700 font-medium text-center bg-green-50 rounded-md px-3 py-2">
              Constructor selection complete ✓
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
```

### Step 4: Enhanced DrsBoostSelector Component

**File:** `src/components/teams/DrsBoostSelector.tsx`

**Design Notes:**
- Only shows after drivers are selected (progressive disclosure)
- Radio buttons are large and touch-friendly
- DRS icon makes it feel special
- Clear visual hierarchy

```typescript
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import { Driver } from '@/types/driver'
import { Zap } from 'lucide-react'

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
      <Card className="opacity-50">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Zap className="h-5 w-5" aria-hidden="true" />
            DRS Boost
          </CardTitle>
          <CardDescription>
            Select drivers first to assign DRS Boost
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const isComplete = drsBoostDriverId !== null

  return (
    <Card className={isComplete ? 'ring-2 ring-green-200' : ''}>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Zap className="h-5 w-5 text-yellow-600" aria-hidden="true" />
          DRS Boost
          {isComplete && <span className="text-green-600 text-sm font-normal">✓</span>}
        </CardTitle>
        <CardDescription>
          Choose one driver to boost with DRS
        </CardDescription>
      </CardHeader>

      <CardContent>
        <RadioGroup value={drsBoostDriverId || ''} onValueChange={onDrsBoostChange}>
          <div className="space-y-2">
            {selectedDrivers.map((driver) => (
              <div
                key={driver.driver_id}
                className={`
                  flex items-center space-x-3 rounded-lg border-2 p-3 transition-all
                  ${drsBoostDriverId === driver.driver_id
                    ? 'border-yellow-400 bg-yellow-50'
                    : 'border-border hover:bg-muted'
                  }
                `}
              >
                <RadioGroupItem
                  value={driver.driver_id}
                  id={driver.driver_id}
                  aria-label={`Assign DRS Boost to ${driver.first_name} ${driver.last_name}`}
                />
                <Label
                  htmlFor={driver.driver_id}
                  className="flex-1 cursor-pointer font-medium"
                >
                  {driver.first_name} {driver.last_name}
                </Label>
                {drsBoostDriverId === driver.driver_id && (
                  <Zap className="h-4 w-4 text-yellow-600 fill-yellow-600" aria-hidden="true" />
                )}
              </div>
            ))}
          </div>
        </RadioGroup>

        {isComplete && (
          <p className="mt-4 text-sm text-green-700 font-medium text-center bg-green-50 rounded-md px-3 py-2">
            DRS Boost assigned ✓
          </p>
        )}
      </CardContent>
    </Card>
  )
}
```

### Step 5: Enhanced ValidationErrors Component

**File:** `src/components/teams/ValidationErrors.tsx`

**Design Notes:**
- Errors fade in, never jump
- List is scannable
- Actionable (tells user what to fix)
- Not shouty, but clear

```typescript
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'

interface ValidationErrorsProps {
  errors: string[]
}

export const ValidationErrors = ({ errors }: ValidationErrorsProps) => {
  if (errors.length === 0) return null

  return (
    <Alert variant="destructive" className="animate-in fade-in slide-in-from-top-2 duration-300">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle className="font-semibold">Please complete the following:</AlertTitle>
      <AlertDescription>
        <ul className="list-disc list-inside mt-2 space-y-1 text-sm">
          {errors.map((error, index) => (
            <li key={index}>{error}</li>
          ))}
        </ul>
      </AlertDescription>
    </Alert>
  )
}
```

### Step 6: Enhanced TeamCreate Page

**File:** `src/pages/TeamCreate.tsx`

**Design Notes:**
- Mobile: vertical stack, budget at top
- Desktop: budget sidebar (sticky), pickers in main area
- Form sections have clear visual separation
- Submit button is prominent, disabled state is obvious
- Success redirects smoothly

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
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/')}
          className="gap-2"
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
        <Card className="shadow-sm">
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
            className="min-w-[200px] shadow-sm"
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
          >
            Cancel
          </Button>

          {/* Progress Indicator */}
          <div className="ml-auto text-sm text-muted-foreground">
            {isValid ? (
              <span className="text-green-600 font-medium">✓ Ready to create</span>
            ) : (
              <span>Complete all fields to continue</span>
            )}
          </div>
        </div>
      </form>
    </div>
  )
}
```

---

## Design Testing Checklist

### Progressive Disclosure
- [ ] Form reveals sections in logical order
- [ ] DRS Boost hidden until drivers selected
- [ ] Budget summary always visible (sticky sidebar on desktop)
- [ ] No overwhelming "wall of form"

### Visual Hierarchy
- [ ] Team name input is clear first step
- [ ] Selection count badges are unmissable
- [ ] Budget numbers are large and prominent
- [ ] Submit button is primary action

### Real-Time Feedback
- [ ] Budget updates instantly when selections change
- [ ] Selection counts update immediately
- [ ] Validation errors appear/disappear smoothly (fade in/out)
- [ ] Progress indicator shows completion status

### Error Prevention
- [ ] Can't select 6th driver (disabled state is clear)
- [ ] Can't select 3rd constructor (disabled state is clear)
- [ ] Budget bar turns red when over budget
- [ ] Submit button disabled until form valid

### Interaction Design
- [ ] Selections feel immediate (no lag)
- [ ] Selected items have distinct visual state
- [ ] Hover states on all interactive elements
- [ ] Disabled states are obvious with visual feedback
- [ ] Touch targets minimum 44px on mobile

### Responsive Design
- [ ] Mobile: Vertical stack, budget at top, one column
- [ ] Tablet: Two columns (budget + pickers)
- [ ] Desktop: Sidebar budget (sticky), main area for pickers
- [ ] No horizontal scroll at any viewport
- [ ] Search input and filters stack on mobile

### Accessibility
- [ ] Form has clear focus order (name → drivers → constructors → DRS → submit)
- [ ] All interactive elements keyboard accessible
- [ ] Selection states announced to screen readers
- [ ] Error messages associated with form fields
- [ ] ARIA labels on all icons and counts

### States & Animations
- [ ] Loading state shows spinner with message
- [ ] Validation errors fade in smoothly (200ms)
- [ ] Budget bar animates when changing (300ms)
- [ ] Success toast appears before redirect
- [ ] Transitions feel natural, not jarring

---

## Acceptance Criteria

✅ **Feature is design-complete when:**

1. Form feels like a guided conversation, not a wall of inputs
2. Progressive disclosure keeps complexity manageable
3. Budget feedback is instant and clear
4. Selection states are visually distinct
5. Error prevention stops mistakes before they happen
6. Validation messages are helpful, not hostile
7. Responsive layout works fluidly on all devices
8. Animations are purposeful and enhance UX
9. Accessibility passes keyboard and screen reader tests
10. The form feels inevitable — no other design was possible

**The Jobs Test:**
- Can a first-time user complete this form without instructions? → YES
- Does every element serve the user's goal? → YES
- Can anything be removed without losing clarity? → NO

---

## Definition of Done

- [ ] All design testing checklist items pass
- [ ] Form can be completed on mobile without zooming
- [ ] Budget updates with < 100ms latency
- [ ] All transitions feel natural (tested across devices)
- [ ] Error messages guide user to fix, never blame
- [ ] Success flow (create → redirect) feels smooth
- [ ] DESIGN_SYSTEM.md tokens used exclusively
- [ ] Accessibility tested with keyboard + screen reader
- [ ] Screenshots captured for each key state
- [ ] LESSONS.md updated with form design patterns learned

**This is the most complex feature. Perfect it before moving on.**
