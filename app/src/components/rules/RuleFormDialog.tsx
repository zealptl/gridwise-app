import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { Rule, RuleCreate, RuleUpdate, RuleType, RuleSeverity } from '@/types/rule'

interface RuleFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  rule?: Rule | null
  onSubmit: (data: RuleCreate | RuleUpdate) => Promise<void>
}

const RULE_TYPES: { value: RuleType; label: string }[] = [
  { value: 'budget_cap', label: 'Budget Cap' },
  { value: 'roster_size', label: 'Roster Size' },
  { value: 'drs_boost_required', label: 'DRS Boost Required' },
  { value: 'max_teams_per_user', label: 'Max Teams Per User' },
  { value: 'transfer_limit', label: 'Transfer Limit' },
  { value: 'driver_eligibility', label: 'Driver Eligibility' },
]

const SEVERITIES: { value: RuleSeverity; label: string }[] = [
  { value: 'error', label: 'Error' },
  { value: 'warning', label: 'Warning' },
  { value: 'info', label: 'Info' },
]

interface FormState {
  name: string
  description: string
  rule_type: RuleType | ''
  severity: RuleSeverity
  applies_to: string
  config: string
  vl_operator: string
  vl_field: string
  vl_threshold: string
  vl_error_message_template: string
  vl_function: string
}

const emptyForm: FormState = {
  name: '',
  description: '',
  rule_type: '',
  severity: 'error',
  applies_to: 'team',
  config: '{}',
  vl_operator: '',
  vl_field: '',
  vl_threshold: '',
  vl_error_message_template: '',
  vl_function: '',
}

function ruleToForm(rule: Rule): FormState {
  return {
    name: rule.name,
    description: rule.description,
    rule_type: rule.rule_type,
    severity: rule.severity,
    applies_to: rule.applies_to,
    config: JSON.stringify(rule.config, null, 2),
    vl_operator: rule.validation_logic.operator,
    vl_field: rule.validation_logic.field,
    vl_threshold: rule.validation_logic.threshold,
    vl_error_message_template: rule.validation_logic.error_message_template,
    vl_function: rule.validation_logic.function ?? '',
  }
}

export function RuleFormDialog({ open, onOpenChange, rule, onSubmit }: RuleFormDialogProps) {
  const isEdit = !!rule
  const [form, setForm] = useState<FormState>(emptyForm)
  const [configError, setConfigError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({})

  useEffect(() => {
    if (open) {
      setForm(rule ? ruleToForm(rule) : emptyForm)
      setConfigError(null)
      setErrors({})
    }
  }, [open, rule])

  const set = (field: keyof FormState, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }))

  const validate = (): boolean => {
    const next: typeof errors = {}
    if (!form.name.trim()) next.name = 'Name is required'
    if (!form.description.trim()) next.description = 'Description is required'
    if (!isEdit && !form.rule_type) next.rule_type = 'Rule type is required'
    if (!form.applies_to.trim()) next.applies_to = 'Applies to is required'
    if (!form.vl_operator.trim()) next.vl_operator = 'Operator is required'
    if (!form.vl_field.trim()) next.vl_field = 'Field is required'
    if (!form.vl_threshold.trim()) next.vl_threshold = 'Threshold is required'
    if (!form.vl_error_message_template.trim()) next.vl_error_message_template = 'Error message is required'

    try {
      JSON.parse(form.config)
      setConfigError(null)
    } catch {
      setConfigError('Invalid JSON')
      next.config = 'Invalid JSON'
    }

    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    const validation_logic = {
      operator: form.vl_operator,
      field: form.vl_field,
      threshold: form.vl_threshold,
      error_message_template: form.vl_error_message_template,
      ...(form.vl_function ? { function: form.vl_function } : {}),
    }
    const config = JSON.parse(form.config)

    const payload: RuleCreate | RuleUpdate = isEdit
      ? {
          name: form.name,
          description: form.description,
          severity: form.severity,
          config,
          validation_logic,
        }
      : {
          name: form.name,
          description: form.description,
          rule_type: form.rule_type as RuleType,
          severity: form.severity,
          applies_to: form.applies_to,
          config,
          validation_logic,
        }

    setSubmitting(true)
    try {
      await onSubmit(payload)
      onOpenChange(false)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit Rule' : 'Create Rule'}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5 pt-2">
          {/* Basic Info */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Basic Info
            </h3>

            <div className="grid grid-cols-1 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="rule-name">Name</Label>
                <Input
                  id="rule-name"
                  value={form.name}
                  onChange={(e) => set('name', e.target.value)}
                  placeholder="e.g. Budget Cap Rule"
                />
                {errors.name && <p className="text-xs text-destructive">{errors.name}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="rule-description">Description</Label>
                <textarea
                  id="rule-description"
                  value={form.description}
                  onChange={(e) => set('description', e.target.value)}
                  placeholder="Describe what this rule validates..."
                  rows={2}
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none"
                />
                {errors.description && <p className="text-xs text-destructive">{errors.description}</p>}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {!isEdit && (
                <div className="space-y-1.5">
                  <Label>Rule Type</Label>
                  <Select value={form.rule_type} onValueChange={(v) => set('rule_type', v)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {RULE_TYPES.map((rt) => (
                        <SelectItem key={rt.value} value={rt.value}>
                          {rt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.rule_type && <p className="text-xs text-destructive">{errors.rule_type}</p>}
                </div>
              )}

              <div className="space-y-1.5">
                <Label>Severity</Label>
                <Select value={form.severity} onValueChange={(v) => set('severity', v as RuleSeverity)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SEVERITIES.map((s) => (
                      <SelectItem key={s.value} value={s.value}>
                        {s.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {!isEdit && (
                <div className="space-y-1.5">
                  <Label htmlFor="rule-applies-to">Applies To</Label>
                  <Input
                    id="rule-applies-to"
                    value={form.applies_to}
                    onChange={(e) => set('applies_to', e.target.value)}
                    placeholder="e.g. team"
                  />
                  {errors.applies_to && <p className="text-xs text-destructive">{errors.applies_to}</p>}
                </div>
              )}
            </div>
          </div>

          {/* Validation Logic */}
          <div className="space-y-4 pt-2 border-t">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Validation Logic
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="vl-operator">Operator</Label>
                <Input
                  id="vl-operator"
                  value={form.vl_operator}
                  onChange={(e) => set('vl_operator', e.target.value)}
                  placeholder="e.g. lte, gte, eq"
                />
                {errors.vl_operator && <p className="text-xs text-destructive">{errors.vl_operator}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="vl-field">Field</Label>
                <Input
                  id="vl-field"
                  value={form.vl_field}
                  onChange={(e) => set('vl_field', e.target.value)}
                  placeholder="e.g. budget_used"
                />
                {errors.vl_field && <p className="text-xs text-destructive">{errors.vl_field}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="vl-threshold">Threshold</Label>
                <Input
                  id="vl-threshold"
                  value={form.vl_threshold}
                  onChange={(e) => set('vl_threshold', e.target.value)}
                  placeholder="e.g. 100000000"
                />
                {errors.vl_threshold && <p className="text-xs text-destructive">{errors.vl_threshold}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="vl-function">Function (optional)</Label>
                <Input
                  id="vl-function"
                  value={form.vl_function}
                  onChange={(e) => set('vl_function', e.target.value)}
                  placeholder="e.g. check_budget"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="vl-error-message">Error Message Template</Label>
              <Input
                id="vl-error-message"
                value={form.vl_error_message_template}
                onChange={(e) => set('vl_error_message_template', e.target.value)}
                placeholder="e.g. Budget exceeds {threshold}"
              />
              {errors.vl_error_message_template && (
                <p className="text-xs text-destructive">{errors.vl_error_message_template}</p>
              )}
            </div>
          </div>

          {/* Config (JSON) */}
          <div className="space-y-2 pt-2 border-t">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Config (JSON)
            </h3>
            <textarea
              value={form.config}
              onChange={(e) => {
                set('config', e.target.value)
                setConfigError(null)
              }}
              rows={4}
              spellCheck={false}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-y"
            />
            {configError && <p className="text-xs text-destructive">{configError}</p>}
          </div>

          <DialogFooter className="pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Rule'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
