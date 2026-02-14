# GridWise Frontend Implementation Plan

## Context

GridWise is an F1 Fantasy Team Management Platform that allows users to create and manage fantasy F1 teams with AI-powered optimization. The backend is fully implemented with FastAPI and MongoDB, providing comprehensive APIs for drivers, constructors, teams, and a sophisticated rule validation engine.

**Current State:**
- Backend: ✅ Fully implemented with all CRUD operations, validation engine, transfer tracking
- Frontend: ❌ Does not exist - starting from scratch

**Why this change is needed:**
Users currently have no way to interact with the backend system. This frontend will provide an intuitive interface for creating teams, managing transfers, viewing validation results, and administering rules.

**Tech Stack:**
- React 18 + TypeScript 5
- Vite (build tool)
- shadcn/ui + Tailwind CSS (UI components)
- Axios (API client)
- React Router DOM 6 (routing)
- React Hook Form 7 (forms)
- Zustand (state management)
- Vitest + React Testing Library (testing)

---

## Implementation Approach

The implementation follows a 10-phase approach, building from foundation to features. Each phase is independently verifiable.

### Phase 0: Project Setup & Configuration
**Goal:** Establish project foundation with all tooling configured

**Steps:**
1. Initialize Vite project with React + TypeScript template in `/app` directory
2. Install dependencies:
   - UI: `tailwindcss`, `shadcn/ui` dependencies, `lucide-react`
   - Routing: `react-router-dom@6`
   - HTTP: `axios`
   - Forms: `react-hook-form@7`, `zod`
   - State: `zustand`
   - Testing: `vitest`, `@testing-library/react`
3. Configure Tailwind CSS with shadcn/ui theme
4. Set up TypeScript path aliases (`@/*` → `./src/*`)
5. Configure ESLint + Prettier
6. Create folder structure:
   ```
   src/
   ├── api/          # API client modules
   ├── components/   # React components
   │   ├── ui/      # shadcn/ui components
   │   ├── layout/  # Layout components
   │   ├── teams/   # Team-specific components
   │   ├── rules/   # Rule-specific components
   │   └── common/  # Shared components
   ├── pages/       # Route pages
   ├── hooks/       # Custom hooks
   ├── stores/      # Zustand stores
   ├── types/       # TypeScript types
   ├── utils/       # Utilities
   └── lib/         # Third-party configs
   ```
7. Set up environment variables (`.env.local` with `VITE_API_BASE_URL=http://localhost:8000/api/v1`)

**Verification:**
```bash
npm run dev  # Should start on http://localhost:5173
npm run build  # Should compile without errors
```

---

### Phase 1: TypeScript Types & API Client Foundation
**Goal:** Create type-safe API layer matching backend schemas

**Key Files to Create:**

**Types** (`/src/types/`):
- `driver.ts` - Driver, DriverCreate, DriverUpdate, PriceHistory interfaces
- `constructor.ts` - Constructor, ConstructorCreate, ConstructorUpdate interfaces
- `team.ts` - FantasyTeam, TeamCreate, TeamUpdate, DriverSelection, ConstructorSelection, TransferRecord, ValidationError, PaginatedTeamsResponse
- `rule.ts` - Rule, RuleCreate, RuleUpdate, RuleType enum, RuleSeverity enum
- `api.ts` - ApiError, ApiResponse generic types

**API Client** (`/src/api/`):
- `client.ts` - Axios instance with interceptors, base URL config, error handling
- `drivers.ts` - driversApi with getAll, getById, create, update, delete, getByTeam
- `constructors.ts` - constructorsApi with CRUD operations
- `teams.ts` - teamsApi with CRUD + pagination
- `rules.ts` - rulesApi with CRUD + toggle

**Verification:**
- TypeScript compilation passes
- Import paths with `@/` resolve correctly
- API client can be imported without errors

---

### Phase 2: State Management & Custom Hooks
**Goal:** Set up global state and data fetching patterns

**Zustand Stores** (`/src/stores/`):
- `teamStore.ts` - teams[], currentTeam, loading, error states + actions
- `ruleStore.ts` - rules[], activeRules, loading, error states + actions

**Custom Hooks** (`/src/hooks/`):
- `useDrivers.ts` - Fetch drivers with optional filters (team_name, status)
- `useConstructors.ts` - Fetch constructors with optional filters
- `useTeams.ts` - Fetch teams with pagination + filters, integrates with teamStore
- `useBudgetCalculator.ts` - **Critical** - Real-time budget calculation (budgetUsed, budgetRemaining, isOverBudget, budgetPercentage)
- `useTeamValidation.ts` - Client-side validation (5 drivers, 2 constructors, DRS boost, budget)

**Why Zustand:**
- Simpler than Redux (no boilerplate)
- Better performance than Context API (avoids unnecessary re-renders)
- Easy testing and debugging
- Small bundle size (1.2kB)

**Verification:**
- Stores accessible from components
- Hooks fetch and return data correctly
- Budget calculator computes in real-time

---

### Phase 3: UI Component Library Setup
**Goal:** Install shadcn/ui and create common components

**Steps:**
1. Run `npx shadcn-ui@latest init`
2. Add components: `button`, `card`, `input`, `label`, `select`, `dialog`, `toast`, `switch`, `tabs`, `table`, `badge`, `alert`, `skeleton`, `tooltip`, `progress`, `checkbox`, `radio-group`
3. Create common components:
   - `LoadingSpinner.tsx` - Reusable loading indicator
   - `ErrorDisplay.tsx` - Error alert with retry button
   - `EmptyState.tsx` - Empty state with icon and action

**Verification:**
- All shadcn/ui components in `/src/components/ui/`
- Common components render correctly
- Theme applies across all components

---

### Phase 4: Routing & Layout Structure
**Goal:** Set up navigation and page shells

**Layout Components** (`/src/components/layout/`):
- `Header.tsx` - Header with logo, navigation links (Teams, Rules)
- `Layout.tsx` - Main layout wrapper with Header + Outlet

**App Router** (`/src/App.tsx`):
```
/ - Dashboard (team list)
/teams/create - Team creation form
/teams/:id - Team detail view
/teams/:id/edit - Team edit form
/admin/rules - Rules management
```

**Page Shells** (`/src/pages/`):
- `Dashboard.tsx`
- `TeamCreate.tsx`
- `TeamDetail.tsx`
- `TeamEdit.tsx`
- `RulesAdmin.tsx`

**Verification:**
- Navigate to http://localhost:5173
- Header displays with working links
- All routes navigate correctly

---

### Phase 5: Dashboard - Team List View
**Goal:** Display teams with filtering and pagination

**Components:**
- `TeamCard.tsx` - Card showing team summary (name, season, budget, validation status, action buttons)

**Dashboard Features:**
- Fetch teams with `useTeams` hook
- Filter by season (2026, 2025)
- Filter by validation status (all, valid only, invalid only)
- Grid layout (responsive: 1 col mobile, 2 cols tablet, 3 cols desktop)
- "Create Team" button
- Loading/error/empty states

**Verification:**
- Dashboard displays team cards
- Filters update the list
- Create button navigates to `/teams/create`

---

### Phase 6: Team Creation Form ⭐ (Most Complex)
**Goal:** Build complete team creation experience with real-time validation

**Critical Components:**

1. **`DriverSelector.tsx`** - Multi-select with:
   - Search by name
   - Filter by F1 team
   - Visual selection state
   - Max 5 drivers limit
   - Display price

2. **`ConstructorSelector.tsx`** - Multi-select for 2 constructors

3. **`BudgetDisplay.tsx`** - Real-time budget tracking:
   - Progress bar (100M cap)
   - Used/Remaining display
   - Over-budget warning (red styling)

4. **`DrsBoostSelector.tsx`** - Radio group for selecting DRS boost driver (must be from selected drivers)

5. **`ValidationErrors.tsx`** - Alert displaying validation errors

**Team Creation Flow:**
1. User enters team name
2. Selects 5 drivers (with search/filter)
3. Selects 2 constructors
4. Assigns DRS boost to one driver
5. Real-time validation checks:
   - Exactly 5 drivers ✓
   - Exactly 2 constructors ✓
   - DRS boost assigned ✓
   - Budget ≤ 100M ✓
6. Submit button disabled until valid
7. On submit → POST `/api/v1/teams` → redirect to team detail

**Verification:**
- Form loads with driver/constructor data
- Selections update budget in real-time
- Validation errors display correctly
- Form submission creates team and redirects

---

### Phase 7: Team Detail & Edit Pages
**Goal:** View team details and make updates with transfer tracking

**Components:**

1. **`TeamDetailView.tsx`** - Display:
   - Team name, season, validation status
   - Budget summary (cap, used, remaining)
   - Driver list with DRS boost indicator (⚡ icon)
   - Constructor list
   - Validation errors (if invalid)

2. **`TransferHistory.tsx`** - Show:
   - Transfer date/time
   - Transfers used/available
   - Penalty points (if exceeded free transfers)
   - Change details

**Team Edit Flow:**
1. Fetch existing team data
2. Pre-populate form with current selections
3. Track changes (drivers added/removed, constructors changed)
4. Calculate transfer count (changes from original)
5. Show warning if exceeding 2 free transfers (-10 points each)
6. On submit → PUT `/api/v1/teams/:id` → redirect to detail

**Verification:**
- Detail page displays all team info
- Edit page pre-populates correctly
- Updates track transfers and calculate penalties
- Transfer history displays

---

### Phase 8: Rules Admin Page
**Goal:** Manage rule validation system

**Components:**

1. **`RuleCard.tsx`** - Display:
   - Rule name, description
   - Rule type, severity badge
   - Active toggle switch
   - Edit/Delete buttons

**Rules Admin Features:**
- Display all rules in grid
- Toggle active/inactive status (PATCH `/rules/:id/toggle`)
- Delete rule with confirmation (soft delete)
- Filter by rule type, active status

**Verification:**
- Rules display in cards
- Toggle activates/deactivates rules
- Delete works with confirmation

---

### Phase 9: Testing Setup
**Goal:** Establish test coverage for critical paths

**Configure Vitest:**
- Update `vite.config.ts` with test configuration
- Create `/src/test/setup.ts` with jest-dom

**Test Coverage:**
- API client functions (drivers, constructors, teams)
- Custom hooks (useBudgetCalculator, useTeamValidation)
- Critical components (BudgetDisplay, DriverSelector, TeamCard)

**Example Test:**
```typescript
describe('useBudgetCalculator', () => {
  it('calculates budget correctly', () => {
    const { budgetUsed, budgetRemaining } = useBudgetCalculator({
      selectedDrivers: [{ price: 10.0 }, { price: 15.0 }],
      selectedConstructors: [{ price: 20.0 }],
      budgetCap: 100.0
    })
    expect(budgetUsed).toBe(45.0)
    expect(budgetRemaining).toBe(55.0)
  })
})
```

**Verification:**
- Run `npm run test`
- Tests pass
- Coverage report generated

---

### Phase 10: Polish & Optimization
**Goal:** Production-ready refinements

**Enhancements:**
1. Add loading skeletons (shadcn/ui Skeleton)
2. Optimize re-renders with React.memo on expensive components
3. Add error boundaries for route-level error handling
4. Implement toast notifications for user feedback
5. Accessibility improvements:
   - ARIA labels
   - Keyboard navigation
   - Focus management
6. Performance optimizations:
   - Memoize expensive calculations
   - Lazy load routes
   - Image optimization

**Verification:**
- Lighthouse score > 90
- No console errors/warnings
- Accessible via keyboard navigation

---

## Critical Files to Modify/Create

**Priority 1 (Foundation):**
1. `/app/src/api/client.ts` - Core Axios client; all API calls depend on this
2. `/app/src/types/team.ts` - Complete team-related TypeScript definitions
3. `/app/src/hooks/useBudgetCalculator.ts` - Real-time budget calculation logic

**Priority 2 (Core Features):**
4. `/app/src/pages/TeamCreate.tsx` - Most complex page, integrates all team components
5. `/app/src/components/teams/DriverSelector.tsx` - Complex multi-select with search/filter

**Priority 3 (Supporting):**
6. `/app/src/stores/teamStore.ts` - Global team state management
7. `/app/src/components/teams/BudgetDisplay.tsx` - Budget visualization
8. `/app/src/pages/Dashboard.tsx` - Main landing page

---

## Backend Integration Points

**APIs to Consume:**

| Endpoint | Method | Usage |
|----------|--------|-------|
| `/api/v1/drivers` | GET | Fetch active drivers for selection |
| `/api/v1/constructors` | GET | Fetch active constructors for selection |
| `/api/v1/teams` | GET | List all teams with pagination |
| `/api/v1/teams` | POST | Create new team |
| `/api/v1/teams/:id` | GET | Get team details |
| `/api/v1/teams/:id` | PUT | Update team (tracks transfers) |
| `/api/v1/rules` | GET | List rules for admin |
| `/api/v1/rules/:id/toggle` | PATCH | Toggle rule active status |

**Expected Backend Responses:**

- Team creation returns full `FantasyTeam` object with:
  - `is_valid` boolean
  - `validation_errors[]` array
  - `budget_used`, `budget_remaining`
  - `transfer_history[]`

- Team updates automatically calculate:
  - Transfer count
  - Penalty points (-10 per excess transfer)
  - Updated validation status

---

## End-to-End Verification Plan

After all phases complete, test this user journey:

1. ✅ **Create Team:**
   - Navigate to `/teams/create`
   - Search for "Verstappen" in driver selector
   - Select 5 drivers from different teams
   - Select 2 constructors
   - Assign DRS boost
   - Verify budget stays under 100M
   - Submit and verify redirect to detail page

2. ✅ **View Team:**
   - See team name, drivers, constructors
   - Verify DRS boost indicator shows
   - Check validation status is "Valid"
   - View budget breakdown

3. ✅ **Edit Team:**
   - Click "Edit Team"
   - Remove 1 driver, add different driver
   - Remove 1 constructor, add different constructor
   - Submit update
   - Verify transfer history shows 2 changes
   - Verify no penalty (within free transfers)

4. ✅ **Exceed Transfers:**
   - Edit team again
   - Make 3 more changes (total 5 transfers)
   - Submit
   - Verify penalty: -30 points (3 excess transfers × -10)

5. ✅ **Rules Admin:**
   - Navigate to `/admin/rules`
   - Toggle "Budget Cap" rule inactive
   - Return to team creation
   - Verify budget cap still enforced client-side
   - Toggle rule back active

6. ✅ **Validation Errors:**
   - Edit team, remove all drivers
   - Verify validation errors display
   - Verify submit button disabled

---

## Estimated Timeline

- **Phase 0:** 2-3 hours (setup)
- **Phase 1:** 1-2 hours (types + API)
- **Phase 2:** 2 hours (state + hooks)
- **Phase 3:** 1-2 hours (UI components)
- **Phase 4:** 1 hour (routing)
- **Phase 5:** 2 hours (dashboard)
- **Phase 6:** 4-5 hours (team creation) ⭐ Most complex
- **Phase 7:** 3-4 hours (detail + edit)
- **Phase 8:** 2 hours (rules admin)
- **Phase 9:** 3-4 hours (testing)
- **Phase 10:** 2-3 hours (polish)

**Total:** 25-35 hours

---

## Dependencies & Prerequisites

**Before starting:**
- ✅ Backend running on `http://localhost:8000`
- ✅ CORS configured for `http://localhost:5173`
- ✅ Node.js 18+ installed
- ✅ npm or yarn available

**External libraries to install:**
- React 18, TypeScript 5, Vite
- shadcn/ui + dependencies (@radix-ui/*, class-variance-authority, clsx, tailwind-merge)
- Axios, React Router DOM 6, React Hook Form 7, Zustand
- Vitest, @testing-library/react

---

## Open Questions

None - backend is fully implemented and documented. All APIs tested and operational.

---

## Success Criteria

- ✅ Users can create valid F1 fantasy teams
- ✅ Real-time budget calculation and validation
- ✅ Transfer tracking with penalty calculation
- ✅ Mobile-responsive design
- ✅ Accessible (keyboard navigation, ARIA labels)
- ✅ Type-safe (no TypeScript errors)
- ✅ Test coverage > 70% for critical paths
- ✅ Production build < 500KB (gzipped)
