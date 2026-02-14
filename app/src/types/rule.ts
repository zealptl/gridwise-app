export type RuleType =
  | 'budget_cap'
  | 'roster_size'
  | 'drs_boost_required'
  | 'max_teams_per_user'
  | 'transfer_limit'
  | 'driver_eligibility'

export type RuleSeverity = 'error' | 'warning' | 'info'

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
