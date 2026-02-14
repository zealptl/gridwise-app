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
