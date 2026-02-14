# Feature: Dashboard - Team List View

## Overview

Build the main dashboard that displays all fantasy teams with filtering and pagination capabilities.

**Estimated Time:** 2 hours
**Dependencies:** Foundation setup (Phase 0-4) must be complete
**Complexity:** Low-Medium

---

## Feature Requirements

### Functional Requirements
- Display all teams in a responsive grid (1 col mobile, 2 cols tablet, 3 cols desktop)
- Show team summary information (name, season, budget, validation status)
- Filter teams by season (2026, 2025)
- Filter teams by validation status (all, valid only, invalid only)
- Navigate to team detail page
- Navigate to team edit page
- Create new team button
- Handle loading states
- Handle error states
- Handle empty state (no teams)

### UI/UX Requirements
- Clean, card-based design
- Clear visual distinction for valid vs invalid teams
- Responsive layout
- Fast load times
- Accessible (keyboard navigation, screen readers)

---

## Implementation Steps

### Step 1: Create TeamCard Component

**File:** `src/components/teams/TeamCard.tsx`

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { TeamSummary } from '@/types/team'
import { Link } from 'react-router-dom'
import { CheckCircle, XCircle } from 'lucide-react'

interface TeamCardProps {
  team: TeamSummary
}

export const TeamCard = ({ team }: TeamCardProps) => {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <CardTitle className="text-xl">{team.team_name}</CardTitle>
          <Badge variant={team.is_valid ? 'default' : 'destructive'}>
            {team.is_valid ? (
              <><CheckCircle className="h-3 w-3 mr-1" /> Valid</>
            ) : (
              <><XCircle className="h-3 w-3 mr-1" /> Invalid</>
            )}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Season:</span>
            <span className="font-medium">{team.season}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Budget Used:</span>
            <span className="font-medium">{team.budget_used.toFixed(1)}M</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Budget Remaining:</span>
            <span className="font-medium">{team.budget_remaining.toFixed(1)}M</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Drivers:</span>
            <span className="font-medium">{team.driver_count}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Constructors:</span>
            <span className="font-medium">{team.constructor_count}</span>
          </div>
        </div>

        <div className="mt-4 flex gap-2">
          <Button asChild variant="outline" size="sm" className="flex-1">
            <Link to={`/teams/${team.team_id}`}>View Details</Link>
          </Button>
          <Button asChild size="sm" className="flex-1">
            <Link to={`/teams/${team.team_id}/edit`}>Edit</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
```

### Step 2: Update Dashboard Page

**File:** `src/pages/Dashboard.tsx`

```typescript
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { TeamCard } from '@/components/teams/TeamCard'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { EmptyState } from '@/components/common/EmptyState'
import { useTeams } from '@/hooks/useTeams'
import { PlusCircle } from 'lucide-react'

export default function Dashboard() {
  const [season, setSeason] = useState<number | undefined>(2026)
  const [isValid, setIsValid] = useState<boolean | undefined>(undefined)

  const { teams, loading, error, refetch } = useTeams({ season, is_valid: isValid })

  if (loading) {
    return <LoadingSpinner size="lg" className="mt-12" />
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={refetch} />
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">My Teams</h1>
        <Button asChild>
          <Link to="/teams/create">
            <PlusCircle className="h-4 w-4 mr-2" />
            Create Team
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <Select value={season?.toString()} onValueChange={(v) => setSeason(Number(v))}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Season" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="2026">2026</SelectItem>
            <SelectItem value="2025">2025</SelectItem>
          </SelectContent>
        </Select>

        <Select value={isValid?.toString() || 'all'} onValueChange={(v) => {
          if (v === 'all') setIsValid(undefined)
          else setIsValid(v === 'true')
        }}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Teams</SelectItem>
            <SelectItem value="true">Valid Only</SelectItem>
            <SelectItem value="false">Invalid Only</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Team Grid */}
      {teams.length === 0 ? (
        <EmptyState
          title="No teams found"
          description="Create your first fantasy team to get started"
          action={
            <Button asChild>
              <Link to="/teams/create">Create Team</Link>
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
```

---

## Testing Requirements

### Unit Tests

Create `src/components/teams/__tests__/TeamCard.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { TeamCard } from '../TeamCard'
import { TeamSummary } from '@/types/team'

const mockTeam: TeamSummary = {
  team_id: '123',
  team_name: 'Test Team',
  season: 2026,
  budget_used: 75.5,
  budget_remaining: 24.5,
  is_valid: true,
  driver_count: 5,
  constructor_count: 2,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

describe('TeamCard', () => {
  it('renders team information correctly', () => {
    render(
      <BrowserRouter>
        <TeamCard team={mockTeam} />
      </BrowserRouter>
    )

    expect(screen.getByText('Test Team')).toBeInTheDocument()
    expect(screen.getByText('2026')).toBeInTheDocument()
    expect(screen.getByText('75.5M')).toBeInTheDocument()
    expect(screen.getByText('24.5M')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('shows valid badge for valid team', () => {
    render(
      <BrowserRouter>
        <TeamCard team={mockTeam} />
      </BrowserRouter>
    )

    expect(screen.getByText(/Valid/)).toBeInTheDocument()
  })

  it('shows invalid badge for invalid team', () => {
    const invalidTeam = { ...mockTeam, is_valid: false }

    render(
      <BrowserRouter>
        <TeamCard team={invalidTeam} />
      </BrowserRouter>
    )

    expect(screen.getByText(/Invalid/)).toBeInTheDocument()
  })

  it('renders action buttons', () => {
    render(
      <BrowserRouter>
        <TeamCard team={mockTeam} />
      </BrowserRouter>
    )

    expect(screen.getByText('View Details')).toBeInTheDocument()
    expect(screen.getByText('Edit')).toBeInTheDocument()
  })
})
```

### Integration Tests

Create `src/pages/__tests__/Dashboard.test.tsx`:

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Dashboard from '../Dashboard'
import { useTeams } from '@/hooks/useTeams'

// Mock the useTeams hook
jest.mock('@/hooks/useTeams')

const mockUseTeams = useTeams as jest.MockedFunction<typeof useTeams>

describe('Dashboard', () => {
  it('shows loading spinner while fetching teams', () => {
    mockUseTeams.mockReturnValue({
      teams: [],
      loading: true,
      error: null,
      refetch: jest.fn(),
    })

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    expect(screen.getByRole('status')).toBeInTheDocument() // Loading spinner
  })

  it('shows error message when fetch fails', () => {
    mockUseTeams.mockReturnValue({
      teams: [],
      loading: false,
      error: 'Failed to fetch teams',
      refetch: jest.fn(),
    })

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    expect(screen.getByText(/Failed to fetch teams/)).toBeInTheDocument()
  })

  it('shows empty state when no teams exist', () => {
    mockUseTeams.mockReturnValue({
      teams: [],
      loading: false,
      error: null,
      refetch: jest.fn(),
    })

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    expect(screen.getByText(/No teams found/)).toBeInTheDocument()
  })

  it('renders team cards when teams exist', async () => {
    const mockTeams = [
      {
        team_id: '1',
        team_name: 'Team 1',
        season: 2026,
        budget_used: 75.5,
        budget_remaining: 24.5,
        is_valid: true,
        driver_count: 5,
        constructor_count: 2,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
    ]

    mockUseTeams.mockReturnValue({
      teams: mockTeams,
      loading: false,
      error: null,
      refetch: jest.fn(),
    })

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Team 1')).toBeInTheDocument()
    })
  })
})
```

---

## Manual Testing Checklist

Test the following scenarios manually:

### Display Tests
- [ ] Dashboard loads without errors
- [ ] Loading spinner appears briefly while fetching data
- [ ] Team cards display in responsive grid (test mobile, tablet, desktop widths)
- [ ] All team information displays correctly (name, season, budget, counts)
- [ ] Valid teams show green "Valid" badge
- [ ] Invalid teams show red "Invalid" badge

### Filter Tests
- [ ] Season filter defaults to 2026
- [ ] Changing season filter updates the team list
- [ ] Validation status filter defaults to "All Teams"
- [ ] "Valid Only" filter shows only valid teams
- [ ] "Invalid Only" filter shows only invalid teams
- [ ] Filters work together correctly

### Navigation Tests
- [ ] "Create Team" button navigates to `/teams/create`
- [ ] "View Details" button navigates to `/teams/:id`
- [ ] "Edit" button navigates to `/teams/:id/edit`
- [ ] Browser back button works correctly

### Error Handling Tests
- [ ] Stop backend server → verify error message displays
- [ ] Error message has "Try again" button
- [ ] Clicking "Try again" retries the request
- [ ] Restarting backend → clicking retry loads teams

### Empty State Tests
- [ ] With no teams → shows empty state message
- [ ] Empty state shows "Create Team" button
- [ ] Empty state button navigates to create page

---

## Acceptance Criteria

✅ **Feature is complete when:**

1. All team cards render correctly with accurate data
2. Filters update the team list in real-time
3. All navigation links work correctly
4. Loading, error, and empty states display appropriately
5. Layout is responsive on mobile, tablet, and desktop
6. All unit tests pass: `npm run test`
7. All manual tests pass
8. No TypeScript errors
9. No console errors or warnings
10. Code is formatted and linted

---

## Iteration Instructions

**Keep iterating until all tests pass:**

1. **Run tests:** `npm run test`
2. **Fix failing tests** - Read error messages, update code
3. **Verify manually** - Test in browser at http://localhost:5173
4. **Check console** - Fix any errors or warnings
5. **Test responsiveness** - Resize browser to mobile/tablet widths
6. **Repeat** until all acceptance criteria are met

### Common Issues & Solutions

**Issue:** Teams not loading
- **Solution:** Verify backend is running on http://localhost:8000
- **Solution:** Check `.env.local` has correct API URL
- **Solution:** Check browser console for CORS errors

**Issue:** Filters not working
- **Solution:** Verify state is being passed to `useTeams` hook
- **Solution:** Check that `useTeams` hook includes filters in dependency array

**Issue:** Layout not responsive
- **Solution:** Verify Tailwind classes: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
- **Solution:** Test at breakpoints: 640px (md), 1024px (lg)

**Issue:** Tests failing
- **Solution:** Ensure all mocks are properly set up
- **Solution:** Wrap components in `<BrowserRouter>` for routing
- **Solution:** Use `waitFor` for async operations

---

## Definition of Done

- [ ] All code implemented and reviewed
- [ ] All unit tests written and passing
- [ ] All integration tests written and passing
- [ ] Manual testing completed
- [ ] No TypeScript errors
- [ ] No linting errors
- [ ] Responsive design verified
- [ ] Browser console clean (no errors/warnings)
- [ ] Feature works end-to-end with real backend
- [ ] Code committed with clear commit message

**Do not move to the next feature until all items are checked.**
