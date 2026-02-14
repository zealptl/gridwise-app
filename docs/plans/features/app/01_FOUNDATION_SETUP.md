# Foundation Setup - GridWise Frontend

## Overview

This plan covers the foundational setup for the GridWise frontend application. Complete all phases in order before moving to feature implementation.

**Estimated Time:** 7-10 hours
**Phases Covered:** 0-4

---

## Phase 0: Project Setup & Configuration

### Objective
Initialize the Vite + React + TypeScript project with all necessary tooling and dependencies.

### Steps

#### 1. Initialize Vite Project
```bash
cd /Users/zealpatel/development/gridwise/gridwise-app/app
npm create vite@latest . -- --template react-ts
```

#### 2. Install Core Dependencies
```bash
# UI Framework & Styling
npm install tailwindcss postcss autoprefixer
npm install class-variance-authority clsx tailwind-merge
npm install lucide-react

# Routing
npm install react-router-dom@6

# HTTP Client
npm install axios

# Form Management
npm install react-hook-form@7
npm install @hookform/resolvers zod

# State Management
npm install zustand

# UI Components (shadcn/ui dependencies)
npm install @radix-ui/react-dialog
npm install @radix-ui/react-dropdown-menu
npm install @radix-ui/react-label
npm install @radix-ui/react-select
npm install @radix-ui/react-toast
npm install @radix-ui/react-switch
npm install @radix-ui/react-tabs
npm install @radix-ui/react-tooltip
npm install @radix-ui/react-checkbox
npm install @radix-ui/react-radio-group
npm install @radix-ui/react-progress
```

#### 3. Install Dev Dependencies
```bash
npm install -D @types/node
npm install -D eslint @typescript-eslint/eslint-plugin @typescript-eslint/parser
npm install -D prettier eslint-config-prettier eslint-plugin-prettier
npm install -D @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm install -D vitest jsdom @vitest/ui
```

#### 4. Initialize Tailwind CSS
```bash
npx tailwindcss init -p
```

Update `tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
}
```

#### 5. Configure TypeScript

Update `tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

Update `vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})
```

#### 6. Create Folder Structure
```bash
mkdir -p src/{api,components/{ui,layout,teams,rules,common},pages,hooks,stores,types,utils,lib,test}
```

#### 7. Environment Configuration

Create `.env.example`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Create `.env.local`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Update `.gitignore` to include `.env.local`

#### 8. ESLint & Prettier

Create `.eslintrc.cjs`:
```javascript
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
    'prettier'
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh', 'prettier'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    'prettier/prettier': 'error'
  },
}
```

Create `.prettierrc`:
```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "arrowParens": "avoid"
}
```

#### 9. Global Styles

Update `src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

#### 10. Test Setup

Create `src/test/setup.ts`:
```typescript
import '@testing-library/jest-dom'
```

### Verification
```bash
npm run dev          # Should start dev server on port 5173
npm run build        # Should compile without errors
npm run lint         # Should run ESLint without errors
```

---

## Phase 1: TypeScript Types & API Client

### Objective
Create type-safe API layer that matches backend Pydantic schemas.

### Files to Create

#### `src/types/driver.ts`
```typescript
export interface PriceHistory {
  price: number
  changed_at: string
  changed_by: string
}

export interface Driver {
  driver_id: string
  first_name: string
  last_name: string
  team_name: string
  nationality: string
  driver_number: number
  price: number
  status: 'active' | 'inactive' | 'reserve'
  price_history: PriceHistory[]
  created_at: string
  updated_at: string
}

export interface DriverCreate {
  first_name: string
  last_name: string
  team_name: string
  nationality: string
  driver_number: number
  price: number
  status?: string
}

export interface DriverUpdate {
  first_name?: string
  last_name?: string
  team_name?: string
  nationality?: string
  driver_number?: number
  price?: number
  status?: string
}
```

#### `src/types/constructor.ts`
```typescript
export interface PriceHistory {
  price: number
  changed_at: string
  changed_by: string
}

export interface Constructor {
  constructor_id: string
  name: string
  full_name: string
  nationality: string
  price: number
  status: 'active' | 'inactive'
  price_history: PriceHistory[]
  created_at: string
  updated_at: string
}

export interface ConstructorCreate {
  name: string
  full_name: string
  nationality: string
  price: number
  status?: string
}

export interface ConstructorUpdate {
  name?: string
  full_name?: string
  nationality?: string
  price?: number
  status?: string
}
```

#### `src/types/team.ts`
```typescript
export interface DriverSelection {
  driver_id: string
  driver_name: string
  team_name: string
  price: number
}

export interface ConstructorSelection {
  constructor_id: string
  constructor_name: string
  price: number
}

export interface TransferRecord {
  race_id?: string
  transfers_used: number
  transfers_available: number
  penalty_points: number
  changes: Record<string, any>[]
  timestamp: string
}

export interface ValidationError {
  rule_type: string
  severity: 'error' | 'warning' | 'info'
  message: string
  details?: Record<string, any>
}

export interface FantasyTeam {
  team_id: string
  team_name: string
  created_by: string
  season: number
  drivers: DriverSelection[]
  constructors: ConstructorSelection[]
  drs_boost_driver_id: string | null
  budget_cap: number
  budget_used: number
  budget_remaining: number
  is_valid: boolean
  validation_errors: ValidationError[]
  transfer_history: TransferRecord[]
  current_race_transfers: number
  available_transfers: number
  created_at: string
  updated_at: string
}

export interface TeamCreate {
  team_name: string
  driver_ids: string[]
  constructor_ids: string[]
  drs_boost_driver_id: string
  season?: number
}

export interface TeamUpdate {
  driver_ids: string[]
  constructor_ids: string[]
  drs_boost_driver_id: string
}

export interface TeamSummary {
  team_id: string
  team_name: string
  season: number
  budget_used: number
  budget_remaining: number
  is_valid: boolean
  driver_count: number
  constructor_count: number
  created_at: string
  updated_at: string
}

export interface PaginatedTeamsResponse {
  total: number
  skip: number
  limit: number
  teams: TeamSummary[]
}
```

#### `src/types/rule.ts`
```typescript
export enum RuleType {
  BUDGET_CAP = 'budget_cap',
  ROSTER_SIZE = 'roster_size',
  DRS_BOOST_REQUIRED = 'drs_boost_required',
  MAX_TEAMS_PER_USER = 'max_teams_per_user',
  TRANSFER_LIMIT = 'transfer_limit',
  DRIVER_ELIGIBILITY = 'driver_eligibility'
}

export enum RuleSeverity {
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info'
}

export interface ValidationLogic {
  operator: string
  field: string
  threshold: string
  error_message_template: string
  function?: string
}

export interface Rule {
  rule_id: string
  rule_type: RuleType
  name: string
  description: string
  config: Record<string, any>
  validation_logic: ValidationLogic
  severity: RuleSeverity
  is_active: boolean
  applies_to: string
  created_at: string
  updated_at: string
  created_by: string
  effective_from?: string
  effective_until?: string
}

export interface RuleCreate {
  rule_type: RuleType
  name: string
  description: string
  config: Record<string, any>
  validation_logic: ValidationLogic
  severity?: RuleSeverity
  applies_to: string
  is_active?: boolean
}

export interface RuleUpdate {
  name?: string
  description?: string
  config?: Record<string, any>
  validation_logic?: ValidationLogic
  severity?: RuleSeverity
  is_active?: boolean
}
```

#### `src/types/api.ts`
```typescript
export interface ApiError {
  detail: string
  status_code?: number
}

export interface ApiResponse<T> {
  data: T
  error?: ApiError
}
```

#### `src/api/client.ts`
```typescript
import axios, { AxiosError, AxiosInstance } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  config => {
    return config
  },
  error => Promise.reject(error)
)

// Response interceptor
apiClient.interceptors.response.use(
  response => response,
  (error: AxiosError) => {
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data)
    } else if (error.request) {
      console.error('Network Error:', error.message)
    } else {
      console.error('Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export default apiClient
```

#### `src/api/drivers.ts`
```typescript
import apiClient from './client'
import { Driver, DriverCreate, DriverUpdate } from '@/types/driver'

export const driversApi = {
  getAll: async (params?: {
    team_name?: string
    status?: string
    skip?: number
    limit?: number
  }): Promise<Driver[]> => {
    const response = await apiClient.get('/drivers', { params })
    return response.data
  },

  getById: async (driverId: string): Promise<Driver> => {
    const response = await apiClient.get(`/drivers/${driverId}`)
    return response.data
  },

  create: async (data: DriverCreate): Promise<Driver> => {
    const response = await apiClient.post('/drivers', data)
    return response.data
  },

  update: async (driverId: string, data: DriverUpdate): Promise<Driver> => {
    const response = await apiClient.put(`/drivers/${driverId}`, data)
    return response.data
  },

  delete: async (driverId: string): Promise<void> => {
    await apiClient.delete(`/drivers/${driverId}`)
  },

  getByTeam: async (teamName: string): Promise<Driver[]> => {
    const response = await apiClient.get(`/drivers/team/${teamName}`)
    return response.data
  },
}
```

#### `src/api/constructors.ts`
```typescript
import apiClient from './client'
import { Constructor, ConstructorCreate, ConstructorUpdate } from '@/types/constructor'

export const constructorsApi = {
  getAll: async (params?: {
    status?: string
    skip?: number
    limit?: number
  }): Promise<Constructor[]> => {
    const response = await apiClient.get('/constructors', { params })
    return response.data
  },

  getById: async (constructorId: string): Promise<Constructor> => {
    const response = await apiClient.get(`/constructors/${constructorId}`)
    return response.data
  },

  create: async (data: ConstructorCreate): Promise<Constructor> => {
    const response = await apiClient.post('/constructors', data)
    return response.data
  },

  update: async (constructorId: string, data: ConstructorUpdate): Promise<Constructor> => {
    const response = await apiClient.put(`/constructors/${constructorId}`, data)
    return response.data
  },

  delete: async (constructorId: string): Promise<void> => {
    await apiClient.delete(`/constructors/${constructorId}`)
  },
}
```

#### `src/api/teams.ts`
```typescript
import apiClient from './client'
import { FantasyTeam, TeamCreate, TeamUpdate, PaginatedTeamsResponse } from '@/types/team'

export const teamsApi = {
  getAll: async (params?: {
    created_by?: string
    season?: number
    is_valid?: boolean
    is_active?: boolean
    skip?: number
    limit?: number
  }): Promise<PaginatedTeamsResponse> => {
    const response = await apiClient.get('/teams', { params })
    return response.data
  },

  getById: async (teamId: string): Promise<FantasyTeam> => {
    const response = await apiClient.get(`/teams/${teamId}`)
    return response.data
  },

  create: async (data: TeamCreate): Promise<FantasyTeam> => {
    const response = await apiClient.post('/teams', data)
    return response.data
  },

  update: async (teamId: string, data: TeamUpdate): Promise<FantasyTeam> => {
    const response = await apiClient.put(`/teams/${teamId}`, data)
    return response.data
  },
}
```

#### `src/api/rules.ts`
```typescript
import apiClient from './client'
import { Rule, RuleCreate, RuleUpdate, RuleType } from '@/types/rule'

export const rulesApi = {
  getAll: async (params?: {
    is_active?: boolean
    rule_type?: RuleType
  }): Promise<Rule[]> => {
    const response = await apiClient.get('/rules', { params })
    return response.data
  },

  getById: async (ruleId: string): Promise<Rule> => {
    const response = await apiClient.get(`/rules/${ruleId}`)
    return response.data
  },

  create: async (data: RuleCreate): Promise<Rule> => {
    const response = await apiClient.post('/rules', data)
    return response.data
  },

  update: async (ruleId: string, data: RuleUpdate): Promise<Rule> => {
    const response = await apiClient.put(`/rules/${ruleId}`, data)
    return response.data
  },

  delete: async (ruleId: string): Promise<void> => {
    await apiClient.delete(`/rules/${ruleId}`)
  },

  toggle: async (ruleId: string): Promise<Rule> => {
    const response = await apiClient.patch(`/rules/${ruleId}/toggle`)
    return response.data
  },
}
```

### Verification
- TypeScript compilation passes: `npm run build`
- No import errors
- API client can be imported in test files

---

## Phase 2: State Management & Custom Hooks

### Objective
Set up Zustand stores and custom React hooks for data fetching.

### Files to Create

#### `src/stores/teamStore.ts`
```typescript
import { create } from 'zustand'
import { FantasyTeam, TeamSummary } from '@/types/team'

interface TeamState {
  teams: TeamSummary[]
  currentTeam: FantasyTeam | null
  loading: boolean
  error: string | null

  setTeams: (teams: TeamSummary[]) => void
  setCurrentTeam: (team: FantasyTeam | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
}

export const useTeamStore = create<TeamState>((set) => ({
  teams: [],
  currentTeam: null,
  loading: false,
  error: null,

  setTeams: (teams) => set({ teams }),
  setCurrentTeam: (team) => set({ currentTeam: team }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}))
```

#### `src/stores/ruleStore.ts`
```typescript
import { create } from 'zustand'
import { Rule } from '@/types/rule'

interface RuleState {
  rules: Rule[]
  activeRules: Rule[]
  loading: boolean
  error: string | null

  setRules: (rules: Rule[]) => void
  setActiveRules: (rules: Rule[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useRuleStore = create<RuleState>((set) => ({
  rules: [],
  activeRules: [],
  loading: false,
  error: null,

  setRules: (rules) => set({ rules }),
  setActiveRules: (rules) => set({ activeRules: rules }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}))
```

#### `src/hooks/useDrivers.ts`
```typescript
import { useState, useEffect } from 'react'
import { driversApi } from '@/api/drivers'
import { Driver } from '@/types/driver'

export const useDrivers = (filters?: { team_name?: string; status?: string }) => {
  const [drivers, setDrivers] = useState<Driver[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchDrivers = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await driversApi.getAll(filters)
        setDrivers(data)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to fetch drivers')
      } finally {
        setLoading(false)
      }
    }

    fetchDrivers()
  }, [filters?.team_name, filters?.status])

  return { drivers, loading, error }
}
```

#### `src/hooks/useConstructors.ts`
```typescript
import { useState, useEffect } from 'react'
import { constructorsApi } from '@/api/constructors'
import { Constructor } from '@/types/constructor'

export const useConstructors = (filters?: { status?: string }) => {
  const [constructors, setConstructors] = useState<Constructor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchConstructors = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await constructorsApi.getAll(filters)
        setConstructors(data)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to fetch constructors')
      } finally {
        setLoading(false)
      }
    }

    fetchConstructors()
  }, [filters?.status])

  return { constructors, loading, error }
}
```

#### `src/hooks/useTeams.ts`
```typescript
import { useState, useEffect, useCallback } from 'react'
import { teamsApi } from '@/api/teams'
import { useTeamStore } from '@/stores/teamStore'

export const useTeams = (filters?: {
  season?: number
  is_valid?: boolean
  skip?: number
  limit?: number
}) => {
  const { teams, setTeams, loading, setLoading, error, setError } = useTeamStore()

  const fetchTeams = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await teamsApi.getAll(filters)
      setTeams(data.teams)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch teams')
    } finally {
      setLoading(false)
    }
  }, [filters, setTeams, setLoading, setError])

  useEffect(() => {
    fetchTeams()
  }, [fetchTeams])

  return { teams, loading, error, refetch: fetchTeams }
}
```

#### `src/hooks/useBudgetCalculator.ts`
```typescript
import { useMemo } from 'react'
import { Driver } from '@/types/driver'
import { Constructor } from '@/types/constructor'

interface UseBudgetCalculatorProps {
  selectedDrivers: Driver[]
  selectedConstructors: Constructor[]
  budgetCap?: number
}

export const useBudgetCalculator = ({
  selectedDrivers,
  selectedConstructors,
  budgetCap = 100.0,
}: UseBudgetCalculatorProps) => {
  const budgetUsed = useMemo(() => {
    const driverCost = selectedDrivers.reduce((sum, d) => sum + d.price, 0)
    const constructorCost = selectedConstructors.reduce((sum, c) => sum + c.price, 0)
    return driverCost + constructorCost
  }, [selectedDrivers, selectedConstructors])

  const budgetRemaining = useMemo(() => {
    return budgetCap - budgetUsed
  }, [budgetCap, budgetUsed])

  const isOverBudget = useMemo(() => {
    return budgetRemaining < 0
  }, [budgetRemaining])

  const budgetPercentage = useMemo(() => {
    return (budgetUsed / budgetCap) * 100
  }, [budgetUsed, budgetCap])

  return {
    budgetUsed,
    budgetRemaining,
    isOverBudget,
    budgetPercentage,
  }
}
```

#### `src/hooks/useTeamValidation.ts`
```typescript
import { useMemo } from 'react'
import { Driver } from '@/types/driver'
import { Constructor } from '@/types/constructor'

interface UseTeamValidationProps {
  selectedDrivers: Driver[]
  selectedConstructors: Constructor[]
  drsBoostDriverId: string | null
  budgetRemaining: number
}

export const useTeamValidation = ({
  selectedDrivers,
  selectedConstructors,
  drsBoostDriverId,
  budgetRemaining,
}: UseTeamValidationProps) => {
  const errors = useMemo(() => {
    const validationErrors: string[] = []

    if (selectedDrivers.length !== 5) {
      validationErrors.push('You must select exactly 5 drivers')
    }

    if (selectedConstructors.length !== 2) {
      validationErrors.push('You must select exactly 2 constructors')
    }

    if (budgetRemaining < 0) {
      validationErrors.push('Team exceeds budget cap')
    }

    if (selectedDrivers.length > 0 && !drsBoostDriverId) {
      validationErrors.push('You must assign DRS Boost to one driver')
    }

    if (drsBoostDriverId) {
      const hasDriver = selectedDrivers.some(d => d.driver_id === drsBoostDriverId)
      if (!hasDriver) {
        validationErrors.push('DRS Boost must be assigned to a selected driver')
      }
    }

    return validationErrors
  }, [selectedDrivers, selectedConstructors, drsBoostDriverId, budgetRemaining])

  const isValid = errors.length === 0

  return { isValid, errors }
}
```

### Verification
- Stores are accessible from components
- Hooks can be imported without errors
- TypeScript compilation passes

---

## Phase 3: UI Component Library Setup

### Objective
Install shadcn/ui and create common UI components.

### Steps

#### 1. Initialize shadcn/ui
```bash
npx shadcn-ui@latest init
```
Follow prompts:
- TypeScript: Yes
- Style: Default
- Base color: Slate
- CSS variables: Yes
- Tailwind config: tailwind.config.js
- Components location: @/components/ui
- Utils location: @/lib/utils

#### 2. Add shadcn/ui Components
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add label
npx shadcn-ui@latest add select
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add switch
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add table
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add alert
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add tooltip
npx shadcn-ui@latest add progress
npx shadcn-ui@latest add checkbox
npx shadcn-ui@latest add radio-group
```

#### 3. Create Common Components

**`src/components/common/LoadingSpinner.tsx`:**
```typescript
import { Loader2 } from 'lucide-react'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export const LoadingSpinner = ({ size = 'md', className = '' }: LoadingSpinnerProps) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  }

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <Loader2 className={`animate-spin ${sizeClasses[size]}`} />
    </div>
  )
}
```

**`src/components/common/ErrorDisplay.tsx`:**
```typescript
import { AlertCircle } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

interface ErrorDisplayProps {
  title?: string
  message: string
  onRetry?: () => void
}

export const ErrorDisplay = ({
  title = 'Error',
  message,
  onRetry
}: ErrorDisplayProps) => {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>
        {message}
        {onRetry && (
          <button
            onClick={onRetry}
            className="ml-2 underline"
          >
            Try again
          </button>
        )}
      </AlertDescription>
    </Alert>
  )
}
```

**`src/components/common/EmptyState.tsx`:**
```typescript
import { FileQuestion } from 'lucide-react'

interface EmptyStateProps {
  title: string
  description?: string
  action?: React.ReactNode
}

export const EmptyState = ({ title, description, action }: EmptyStateProps) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <FileQuestion className="h-16 w-16 text-muted-foreground mb-4" />
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground mb-4">{description}</p>
      )}
      {action}
    </div>
  )
}
```

### Verification
- All shadcn/ui components exist in `/src/components/ui/`
- Common components render without errors
- Build passes: `npm run build`

---

## Phase 4: Routing & Layout Structure

### Objective
Set up React Router and create base layout components.

### Files to Create

#### `src/components/layout/Header.tsx`
```typescript
import { Link } from 'react-router-dom'
import { Trophy } from 'lucide-react'

export const Header = () => {
  return (
    <header className="border-b bg-background">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <Trophy className="h-6 w-6 text-primary" />
          <span className="text-xl font-bold">GridWise</span>
        </Link>

        <nav className="flex items-center gap-6">
          <Link to="/" className="text-sm font-medium hover:text-primary">
            Teams
          </Link>
          <Link to="/admin/rules" className="text-sm font-medium hover:text-primary">
            Rules
          </Link>
        </nav>
      </div>
    </header>
  )
}
```

#### `src/components/layout/Layout.tsx`
```typescript
import { Outlet } from 'react-router-dom'
import { Header } from './Header'

export const Layout = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
```

#### Page Shells

**`src/pages/Dashboard.tsx`:**
```typescript
export default function Dashboard() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">My Teams</h1>
    </div>
  )
}
```

**`src/pages/TeamCreate.tsx`:**
```typescript
export default function TeamCreate() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Create New Team</h1>
    </div>
  )
}
```

**`src/pages/TeamDetail.tsx`:**
```typescript
import { useParams } from 'react-router-dom'

export default function TeamDetail() {
  const { id } = useParams()

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Team Details</h1>
      <p>Team ID: {id}</p>
    </div>
  )
}
```

**`src/pages/TeamEdit.tsx`:**
```typescript
import { useParams } from 'react-router-dom'

export default function TeamEdit() {
  const { id } = useParams()

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Edit Team</h1>
      <p>Team ID: {id}</p>
    </div>
  )
}
```

**`src/pages/RulesAdmin.tsx`:**
```typescript
export default function RulesAdmin() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Rules Management</h1>
    </div>
  )
}
```

#### `src/App.tsx`
```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import Dashboard from '@/pages/Dashboard'
import TeamCreate from '@/pages/TeamCreate'
import TeamDetail from '@/pages/TeamDetail'
import TeamEdit from '@/pages/TeamEdit'
import RulesAdmin from '@/pages/RulesAdmin'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/teams/create" element={<TeamCreate />} />
          <Route path="/teams/:id" element={<TeamDetail />} />
          <Route path="/teams/:id/edit" element={<TeamEdit />} />
          <Route path="/admin/rules" element={<RulesAdmin />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
```

### Verification
```bash
npm run dev
# Visit http://localhost:5173
# Should see header and navigation
# All routes should navigate correctly (showing page shells)
```

---

## Foundation Complete Checklist

Before moving to feature implementation, verify:

- [ ] Project runs: `npm run dev` starts on http://localhost:5173
- [ ] Build succeeds: `npm run build` completes without errors
- [ ] Linting passes: `npm run lint` shows no errors
- [ ] TypeScript compiles: No TypeScript errors in IDE
- [ ] All routes navigate correctly
- [ ] Header displays with working links
- [ ] Backend is running on http://localhost:8000
- [ ] CORS is configured for http://localhost:5173
- [ ] Environment variables are set in `.env.local`

---

## Iteration Instructions

**If any phase fails:**

1. **Review error messages carefully** - TypeScript and build errors provide specific file/line information
2. **Check dependencies** - Ensure all npm packages are installed correctly
3. **Verify paths** - Confirm all import paths use `@/` alias correctly
4. **Test incrementally** - After fixing, run `npm run build` and `npm run dev` to verify
5. **Keep iterating** - Fix one error at a time, rebuild, and retest until all checks pass

**Do not proceed to feature implementation until all foundation verification checks are complete.**
