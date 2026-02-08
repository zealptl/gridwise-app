# GridWise MVP Implementation Plans Index

## Overview
This document indexes all implementation plan files for the GridWise MVP project.

---

## Backend Plans (service/)

### ✅ Phase 0: Project Setup
**File:** `features/service/00-project-setup.md`
- Python project initialization with `uv` package manager
- pyproject.toml configuration
- Project structure setup
- FastAPI skeleton
- Development tools (ruff, mypy, pytest)
- Environment configuration

### ✅ Phase 1: Backend Foundation

#### 1.1 Database Setup
**File:** `features/service/01-database-setup.md`
- MongoDB connection with Motor + Beanie
- Database schemas (drivers, constructors, rules, teams, users)
- Seed data creation (20 drivers, 10 constructors, 7 rules)
- Database seeding script

#### 1.2 Rule Management (US-4.1 Backend)
**File:** `features/service/02-rule-management-backend.md`
- Rule model with Beanie ODM
- Abstract base class for rule validators
- 7 concrete rule implementations (budget cap, roster size, DRS boost, etc.)
- RuleEngine orchestrator class
- Rule CRUD API endpoints
- Unit and integration tests

#### 1.3 Driver & Constructor APIs
**File:** `features/service/03-driver-constructor-apis.md`
- Driver CRUD endpoints
- Constructor CRUD endpoints
- Price history tracking
- Filtering and pagination
- Integration tests

### ✅ Phase 2: Team Management Backend

#### 2.1 Create Team (US-1.2 Backend)
**File:** `features/service/04-create-team-backend.md`
- FantasyTeam model
- POST /api/v1/teams endpoint
- Rule engine integration
- Budget calculation
- DRS Boost handling
- Validation error responses

#### 2.2 View Teams (US-1.1 Backend)
**File:** `features/service/05-view-teams-backend.md`
- GET /api/v1/teams (list with filters)
- GET /api/v1/teams/{id} (detail)
- Pagination support
- Filtering by season, validity, user
- Summary vs detail responses

#### 2.3 Update Team (US-1.3 Backend)
**File:** `features/service/06-update-team-backend.md`
- PUT /api/v1/teams/{id} endpoint
- Transfer tracking logic
- Penalty calculation (-10 points per excess transfer)
- DRS Boost changes
- Re-validation
- Transfer history recording

---

## Frontend Plans (app/)

### 📝 Phase 3: Frontend Setup & Implementation

#### Planning Notes
**File:** `features/app/FRONTEND_PLANNING_NOTES.md`
- Summary of frontend plans to be created
- Component inventory
- State management strategy
- API client structure
- TypeScript types needed
- Routing structure
- Testing strategy

#### Detailed Plans (To Be Created)
- `00-frontend-setup.md` - React + TypeScript + Vite setup
- `01-rule-management-frontend.md` - Rules admin UI
- `02-view-teams-frontend.md` - Teams dashboard
- `03-create-team-frontend.md` - Team creation form
- `04-update-team-frontend.md` - Team editing with transfer tracking

---

## Implementation Order

### Recommended Sequence

1. **Phase 0: Project Setup** ⬅️ START HERE
   - Set up Python project with uv
   - Verify environment works

2. **Phase 1.1: Database Setup**
   - Install MongoDB
   - Create models
   - Seed database

3. **Phase 1.2: Rule Management Backend**
   - Build rule engine
   - Implement all 7 rules
   - Test validation logic

4. **Phase 1.3: Driver & Constructor APIs**
   - CRUD endpoints
   - Price tracking

5. **Phase 2.1: Create Team Backend**
   - Team creation endpoint
   - Integrate rule engine
   - Test validation

6. **Phase 2.2: View Teams Backend**
   - List and detail endpoints
   - Filtering and pagination

7. **Phase 2.3: Update Team Backend**
   - Update endpoint
   - Transfer tracking
   - Penalty calculation

8. **Phase 3: Frontend**
   - Set up React app
   - Build UI components
   - Integrate with backend APIs

---

## Plan File Format

Each plan file contains:
- **Overview** - Summary of what's being built
- **Objectives** - Specific goals/deliverables
- **Implementation Approach** - Pseudocode and logic flow
- **Files to Create/Modify** - File structure
- **Diagrams** - PlantUML diagrams for complex flows
- **Testing Strategy** - Test cases and approach
- **Verification Checklist** - How to verify it works
- **Next Steps** - What comes after

---

## How to Use These Plans

### For Each Phase:

1. **Review the plan file** - Understand objectives and approach
2. **Check dependencies** - Ensure previous phases are complete
3. **Set up environment** - Install required tools/packages
4. **Implement step-by-step** - Follow the implementation approach
5. **Test thoroughly** - Run tests, verify checklist
6. **Commit changes** - Git commit with meaningful message
7. **Move to next phase** - Proceed to next plan file

### Reading the Plans:

- **Pseudocode blocks** - High-level logic, not exact code
- **PlantUML diagrams** - Can be rendered with PlantUML tools
- **File paths** - Relative to project root
- **Checklists** - Used to track completion

---

## Dependencies Between Plans

```
00-project-setup
    ↓
01-database-setup
    ↓
02-rule-management ←─┐
03-driver-constructor │
    ↓                 │
04-create-team ───────┘
    ↓
05-view-teams
    ↓
06-update-team
    ↓
Frontend Plans
```

---

## Current Status

- ✅ Backend Phase 0 plan created
- ✅ Backend Phase 1 plans created (3 plans)
- ✅ Backend Phase 2 plans created (3 plans)
- 📝 Frontend plans outlined (details pending)
- ⏳ Implementation not started

---

## Next Actions

1. Review all backend plan files (00-06)
2. Approve plans or request modifications
3. Begin implementation with Phase 0
4. Create detailed frontend plans after backend is complete

---

## Questions or Modifications Needed?

If any plan needs clarification or modification:
1. Note which plan file (e.g., `02-rule-management-backend.md`)
2. Note which section needs changes
3. Describe what should be different
4. Plans will be updated before implementation begins
