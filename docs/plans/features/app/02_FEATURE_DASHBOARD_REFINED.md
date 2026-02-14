# Feature: Dashboard - Team List View (Design-Refined)

## Overview

Build the main dashboard that displays all fantasy teams with filtering and pagination capabilities.

**Estimated Time:** 2 hours
**Dependencies:** Foundation setup (Phase 0-4) must be complete
**Complexity:** Low-Medium

---

## Design Philosophy

This screen is the user's home base. It must feel calm, scannable, and effortless. Users should understand their team status in 2 seconds. The hierarchy is: team name → status → actions. Everything else supports.

### Design Principles Applied
- **Visual Hierarchy:** Team validity status is the most critical information — make it unmissable
- **Density:** Remove all non-essential elements. Every pixel must earn its place
- **Responsive First:** Mobile layout is primary. Desktop enhances, never adds clutter
- **States:** Empty, loading, and error states feel intentional, not broken

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
- **Hierarchy:** Team name is most prominent, status badge is unmissable, budget is secondary
- **Density:** Cards breathe — generous padding creates premium feel
- **Typography:** Clear size hierarchy (name: 20px, metadata: 14px, labels: 12px)
- **Color:** Status uses semantic colors (green=valid, red=invalid), all else is neutral
- **Spacing:** Consistent 24px gaps between cards, 16px internal padding
- **Interaction:** Hover states on cards and buttons feel responsive
- **States:** Loading skeleton preserves layout, empty state guides action
- **Accessibility:** Keyboard navigation, focus states, ARIA labels, 4.5:1 contrast minimum
- **Motion:** Subtle hover lift on cards (2px), 200ms ease-out transitions

---

## Design System Tokens Required

Before implementation, add these to `DESIGN_SYSTEM.md`:

```yaml
# Spacing
spacing-xs: 8px      # Icon gaps, small internal spacing
spacing-sm: 12px     # Compact spacing
spacing-md: 16px     # Card padding, standard spacing
spacing-lg: 24px     # Card gaps, section spacing
spacing-xl: 32px     # Page margins, major sections

# Typography
text-xs: 12px / 16px   # Labels, metadata
text-sm: 14px / 20px   # Body, secondary info
text-base: 16px / 24px # Base body text
text-lg: 18px / 28px   # Subheadings
text-xl: 20px / 28px   # Card titles
text-2xl: 24px / 32px  # Section headings
text-3xl: 30px / 36px  # Page headings

# Colors (Semantic)
success-bg: hsl(142, 76%, 96%)      # Valid team background
success-border: hsl(142, 76%, 36%)  # Valid team border
success-text: hsl(142, 76%, 26%)    # Valid team text

error-bg: hsl(0, 84%, 96%)          # Invalid team background
error-border: hsl(0, 84%, 60%)      # Invalid team border
error-text: hsl(0, 84%, 40%)        # Invalid team text

# Shadows
shadow-card: 0 1px 3px rgba(0,0,0,0.12)
shadow-card-hover: 0 4px 12px rgba(0,0,0,0.15)

# Transitions
transition-fast: 150ms ease-out
transition-base: 200ms ease-out
transition-slow: 300ms ease-out
```

---

## Implementation Steps

### Step 1: Create TeamCard Component (Design-Enhanced)

**File:** `src/components/teams/TeamCard.tsx`

**Design Notes:**
- Card elevation increases on hover (shadow-card → shadow-card-hover)
- Status badge is top-right, always visible, high contrast
- Budget displays as visual progress, not just numbers
- Actions are clearly separated from data (visual hierarchy)
- Touch targets minimum 44x44px for mobile accessibility

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { TeamSummary } from '@/types/team'
import { Link } from 'react-router-dom'
import { CheckCircle, XCircle, Eye, Pencil } from 'lucide-react'

interface TeamCardProps {
  team: TeamSummary
}

export const TeamCard = ({ team }: TeamCardProps) => {
  const budgetPercentage = (team.budget_used / 100) * 100

  return (
    <Card className="group transition-all duration-200 hover:shadow-lg">
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
```

### Step 2: Update Dashboard Page (Design-Enhanced)

**File:** `src/pages/Dashboard.tsx`

**Design Notes:**
- Page header is clear and actionable — title + primary action only
- Filters are compact, left-aligned, visually subordinate to content
- Empty state feels intentional, guides user to first action
- Grid uses consistent spacing tokens
- Loading state uses skeleton screens (preserves layout)

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
```

### Step 3: Enhanced EmptyState Component

**File:** `src/components/common/EmptyState.tsx`

**Design Notes:**
- Feels intentional, not broken
- Icon is large but not overwhelming (96px)
- Text hierarchy is clear
- Action is prominent but not shouty
- Centered, breathing space

```typescript
import { LucideIcon } from 'lucide-react'

interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description?: string
  action?: React.ReactNode
}

export const EmptyState = ({
  icon: Icon,
  title,
  description,
  action
}: EmptyStateProps) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {Icon && (
        <div className="mb-6 rounded-full bg-muted p-6">
          <Icon className="h-12 w-12 text-muted-foreground" aria-hidden="true" />
        </div>
      )}
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      {description && (
        <p className="text-base text-muted-foreground max-w-md mb-6">
          {description}
        </p>
      )}
      {action}
    </div>
  )
}
```

---

## Design Testing Checklist

Test these design aspects in addition to functional requirements:

### Visual Hierarchy
- [ ] Eye lands on team name first
- [ ] Status badge is immediately noticeable
- [ ] Actions are clearly separated from data
- [ ] Page title is most prominent element on screen

### Spacing & Rhythm
- [ ] All spacing uses system tokens (8px, 12px, 16px, 24px, 32px)
- [ ] Cards have consistent 16px internal padding
- [ ] Grid gaps are consistent 24px
- [ ] No elements feel cramped or randomly spaced

### Typography
- [ ] Clear size hierarchy (page title > card title > body > metadata)
- [ ] Line heights provide comfortable reading
- [ ] Font weights establish hierarchy (bold for emphasis, regular for body)
- [ ] Text never feels too dense or too sparse

### Color & Contrast
- [ ] Valid badge passes 4.5:1 contrast ratio
- [ ] Invalid badge passes 4.5:1 contrast ratio
- [ ] All text meets WCAG AA standards
- [ ] Color is purposeful, not decorative

### Interaction Design
- [ ] Cards lift on hover (shadow deepens, subtle 2px translation)
- [ ] Buttons show clear hover/focus states
- [ ] Transitions feel natural (200ms ease-out)
- [ ] Touch targets are minimum 44x44px on mobile

### Responsive Design
- [ ] Mobile (< 768px): Single column, cards stack beautifully
- [ ] Tablet (768px - 1024px): 2 columns, layout feels intentional
- [ ] Desktop (> 1024px): 3 columns, not cramped
- [ ] No horizontal scroll at any viewport
- [ ] Filters stack on mobile, inline on desktop

### States
- [ ] Loading skeleton preserves layout structure
- [ ] Empty state feels helpful, not broken
- [ ] Error state is clear and actionable
- [ ] Each state transition feels smooth

### Accessibility
- [ ] Keyboard navigation works (Tab, Enter, Esc)
- [ ] Focus indicators are visible and clear
- [ ] Screen reader announces status changes
- [ ] ARIA labels on icons and interactive elements
- [ ] Semantic HTML structure

---

## Design Review Questions

Before marking complete, answer these:

1. **Simplicity:** Can anything be removed without losing meaning?
   - Every budget detail? Every metadata field? Is anything redundant?

2. **Hierarchy:** Does the most important thing look the most important?
   - Team status should be unmissable. Is it?

3. **Inevitability:** Does this feel like the only way it could have been designed?
   - Or does it feel like arbitrary choices?

4. **Details:** Are the details users never see as refined as the ones they do?
   - Hover states, focus states, skeleton screens, empty states — all polished?

5. **Feeling:** Does it feel calm, confident, and premium?
   - Or busy, cluttered, and cheap?

---

## Implementation Notes for Build Agent

**Exact Changes Required:**

1. **TeamCard.tsx**
   - Card: Add `transition-all duration-200 hover:shadow-lg` classes
   - Badge: Use semantic variants (default for valid, destructive for invalid)
   - Progress component: Add for budget visualization (height: 8px)
   - Icons: Use lucide-react (CheckCircle, XCircle, Eye, Pencil) at 16px
   - Buttons: Equal width using `flex-1`, separated by 8px gap

2. **Dashboard.tsx**
   - Loading: Replace spinner with skeleton grid (6 cards, 256px height each)
   - Header: text-3xl (30px), font-bold, tracking-tight
   - Filters: Compact width (144px each), 12px gap between
   - Grid: gap-6 (24px), responsive (1/2/3 columns)

3. **EmptyState.tsx**
   - Icon container: 96px circle, muted background, 24px padding
   - Icon size: 48px (h-12 w-12)
   - Title: text-xl (20px), font-semibold
   - Description: text-base (16px), max-width 448px

**Color Values** (reference DESIGN_SYSTEM.md):
- Success: Use existing primary variant
- Error: Use existing destructive variant
- Muted: Use existing muted/muted-foreground tokens

**No Hardcoded Values:**
- All spacing uses Tailwind spacing scale
- All colors reference CSS variables
- All text sizes use Tailwind text scale

---

## Acceptance Criteria

✅ **Feature is design-complete when:**

1. Visual hierarchy is unmistakable (team name > status > actions)
2. All spacing uses system tokens consistently
3. Typography establishes clear hierarchy across all text
4. Colors are semantic and pass WCAG AA contrast
5. Hover states feel responsive and intentional
6. Responsive layout works fluidly at all viewports
7. Loading, empty, and error states feel designed, not broken
8. Accessibility passes keyboard navigation and screen reader tests
9. The design feels calm, confident, and inevitable
10. Nothing can be removed without losing meaning

**The Jobs Test:**
- Would a user need to be told how this works? → NO
- Does this feel inevitable? → YES
- Is every detail refined? → YES

---

## Definition of Done

- [ ] All design testing checklist items pass
- [ ] All design review questions answered affirmatively
- [ ] DESIGN_SYSTEM.md tokens added and approved
- [ ] Implementation matches design spec exactly
- [ ] No rogue values (all spacing/colors reference tokens)
- [ ] Responsive design tested at 375px, 768px, 1024px, 1440px
- [ ] Accessibility tested with keyboard + screen reader
- [ ] Design feels premium, calm, and effortless
- [ ] Screenshots captured for before/after comparison
- [ ] LESSONS.md updated with any design patterns learned

**Do not move to the next feature until design feels absolutely right.**
