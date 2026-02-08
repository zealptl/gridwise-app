# Frontend Planning Notes

## Summary
These are notes for future frontend implementation plans. Detailed plans to be created later.

---

## Plans Needed

### Phase 3: Frontend Setup & Implementation

#### 00-frontend-setup.md
- Initialize React + TypeScript + Vite
- Install shadcn/ui, Tailwind CSS, React Router, Axios
- Set up project structure (pages, components, hooks, api, types, contexts)
- Configure ESLint, Prettier, TypeScript
- Create API client skeleton
- Create TypeScript type definitions (mirror backend schemas)
- Set up environment variables
- Verify dev server runs

#### 01-rule-management-frontend.md
- Build Rules Admin page (list all rules)
- Create rule detail/edit form
- Implement rule toggle (activate/deactivate)
- Implement rule config editing (JSON editor or form)
- Display validation errors
- Connect to backend API endpoints
- Real-time rule status updates

#### 02-view-teams-frontend.md
- Create Teams Dashboard page
- Display team cards with summary (budget, drivers count, validation status)
- Implement filters (season, valid/invalid)
- Create team detail modal/page
- Display full team composition (drivers + constructors)
- Show validation errors if invalid
- Show DRS Boost selection
- Show transfer history

#### 03-create-team-frontend.md
- Create team creation form/wizard
- Driver selection component (select 5 drivers with search/filter)
- Constructor selection component (select 2 constructors)
- Real-time budget calculation display
- DRS Boost selection (radio buttons on selected drivers)
- Real-time validation with error display
- Submit handler with error handling
- Success/error notifications (toast)
- Redirect to team detail on success

#### 04-update-team-frontend.md
- Create team edit form (similar to create)
- Pre-populate with existing team data
- Track changes (highlight what changed)
- Show transfer count and penalty warnings
- Allow DRS Boost changes
- Re-validate on changes
- Submit update with error handling
- Show updated team with transfer history

---

## Key Components to Build

### Layout Components
- `Header.tsx` - Top navigation bar
- `Navigation.tsx` - Side navigation or menu
- `Layout.tsx` - Wrapper with header + content area

### Team Components
- `TeamCard.tsx` - Team summary card for dashboard
- `TeamDetail.tsx` - Full team details view
- `DriverSelector.tsx` - Multi-select driver picker (5 max)
- `ConstructorSelector.tsx` - Multi-select constructor picker (2 max)
- `BudgetDisplay.tsx` - Real-time budget tracker with progress bar
- `ValidationErrors.tsx` - Display validation errors/warnings
- `DrsBoostSelector.tsx` - Radio group for DRS Boost selection
- `TransferHistory.tsx` - Display transfer history table

### Rule Components
- `RulesList.tsx` - Table/list of all rules
- `RuleCard.tsx` - Individual rule card with toggle
- `RuleForm.tsx` - Edit rule configuration
- `RuleConfigEditor.tsx` - JSON editor or structured form

### Common Components
- `LoadingSpinner.tsx`
- `ErrorDisplay.tsx`
- `EmptyState.tsx`
- `ConfirmDialog.tsx`

---

## State Management Strategy

### React Context
- `TeamContext` - Current teams, selected team, loading states
- `RuleContext` - Active rules, rule configurations
- `AppContext` - Global app state (user, settings)

### Custom Hooks
- `useTeams()` - Fetch and manage teams
- `useDrivers()` - Fetch drivers with caching
- `useConstructors()` - Fetch constructors with caching
- `useRules()` - Fetch and manage rules
- `useTeamValidation()` - Real-time validation logic
- `useBudgetCalculator()` - Calculate budget in real-time

---

## API Client Structure

```
src/api/
├── client.ts          # Axios instance with interceptors
├── teams.ts           # GET/POST/PUT teams
├── drivers.ts         # GET drivers
├── constructors.ts    # GET constructors
└── rules.ts           # CRUD rules
```

### API Functions to Implement
```typescript
// teams.ts
getAllTeams(filters)
getTeamById(id)
createTeam(data)
updateTeam(id, data)

// drivers.ts
getAllDrivers(filters)
getDriverById(id)

// constructors.ts
getAllConstructors(filters)
getConstructorById(id)

// rules.ts
getAllRules()
getRuleById(id)
createRule(data)
updateRule(id, data)
toggleRule(id)
```

---

## TypeScript Types Needed

Mirror backend Pydantic schemas:

### Team Types
- `Driver` - Driver selection with price
- `Constructor` - Constructor selection with price
- `FantasyTeam` - Full team model
- `TeamCreate` - Team creation payload
- `TeamUpdate` - Team update payload
- `TransferRecord` - Transfer history entry
- `ValidationError` - Rule violation

### Rule Types
- `Rule` - Full rule model
- `RuleType` - Enum of rule types
- `RuleSeverity` - error | warning | info
- `ValidationLogic` - Validation logic structure

### API Types
- `ApiResponse<T>` - Generic API response wrapper
- `PaginatedResponse<T>` - Paginated list response
- `ApiError` - Error response structure

---

## Routing Structure

```
/                          → Dashboard (list teams)
/teams/create              → Create new team
/teams/:id                 → Team detail view
/teams/:id/edit            → Edit team
/admin/rules               → Rules management (admin)
```

---

## UI/UX Considerations

### Real-time Validation
- Validate team composition as user selects drivers/constructors
- Show budget remaining in real-time
- Highlight validation errors immediately
- Disable submit button if invalid

### User Feedback
- Loading states during API calls
- Success/error toasts for actions
- Confirmation dialogs for destructive actions
- Empty states when no data

### Responsive Design
- Mobile-friendly layout
- Touch-friendly selection controls
- Responsive tables/cards
- Collapsible navigation on mobile

---

## Testing Strategy

### Component Tests
- Test team creation form validation
- Test driver/constructor selection logic
- Test budget calculation
- Test DRS Boost selection

### Integration Tests
- Test full team creation flow
- Test team update flow
- Test rule management CRUD

### E2E Tests (Optional)
- Complete user journey: create → view → edit team
- Admin journey: manage rules → create team with new rules

---

## Styling Approach

- **Utility-first:** Tailwind CSS for styling
- **Component library:** shadcn/ui for base components
- **Consistency:** Design tokens for colors, spacing, typography
- **Dark mode:** (Optional for post-MVP)

---

## Next Steps

1. Complete backend implementation first (Phases 0-2)
2. Test backend APIs thoroughly
3. Create detailed frontend plans based on these notes
4. Implement frontend in phases (setup → rules → teams)
5. Integration testing between frontend and backend
6. Polish and deploy

---

## Dependencies on Backend

Frontend depends on these backend endpoints being ready:
- GET/POST/PUT /api/v1/teams
- GET /api/v1/drivers
- GET /api/v1/constructors
- GET/POST/PUT/DELETE /api/v1/rules
- Validation errors properly structured
- CORS configured for frontend origin
