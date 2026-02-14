# Feature: Rules Administration (Design-Refined)

## Overview

Build the rules management interface for admins to view, toggle, and manage validation rules.

**Estimated Time:** 2 hours
**Dependencies:** Foundation setup
**Complexity:** Low-Medium

---

## Design Philosophy

Admin interfaces are often ugly because designers assume "admins don't care." Wrong. Admins are users too. This interface manages the rules that govern the entire app. It must feel powerful but not chaotic. Scannable, not overwhelming. Every rule's status must be obvious at a glance.

### Design Principles Applied
- **Scannable Hierarchy:** Rule name first, type/status subordinate
- **Status First:** Active/inactive must be unmissable (color + position)
- **Confirmation Culture:** Destructive actions require confirmation, but not annoyingly
- **Visual Consistency:** Same patterns as team cards (familiar, not alien)
- **Dense but Breathing:** Pack information but maintain whitespace
- **Admin ≠ Ugly:** Premium feel, even for admin tools

---

## Feature Requirements

### Functional Requirements
- Display all rules in a grid layout
- Show rule details (name, description, type, severity)
- Toggle rule active/inactive status
- Delete rules with confirmation
- Filter rules by type and active status
- Visual indicators for rule severity (error, warning, info)
- Responsive design

### Business Rules
- Toggling a rule updates its `is_active` status via API
- Deleting a rule is a soft delete (sets `is_active` to false)
- Rules are displayed in cards for easy scanning
- Active rules have a toggle switch in the "on" position

### Design Requirements
- **Status visibility:** Toggle switch + active/inactive label + card styling
- **Severity badges:** Color-coded (red=error, amber=warning, blue=info)
- **Filters:** Compact, always visible, don't dominate the page
- **Confirmation:** Delete confirmation is clear, not scary
- **Empty state:** Helpful when no rules match filters
- **Grid density:** 2 columns on desktop, 1 on mobile

---

## Design System Tokens Required

Add these to `DESIGN_SYSTEM.md`:

```yaml
# Admin-Specific Colors
admin-header-bg: hsl(220, 14%, 96%)
admin-border: hsl(220, 13%, 91%)

# Rule Severity Colors
severity-error-bg: hsl(0, 84%, 96%)
severity-error-text: hsl(0, 84%, 40%)
severity-error-border: hsl(0, 84%, 60%)

severity-warning-bg: hsl(38, 92%, 96%)
severity-warning-text: hsl(38, 92%, 40%)
severity-warning-border: hsl(38, 92%, 60%)

severity-info-bg: hsl(199, 89%, 96%)
severity-info-text: hsl(199, 89%, 40%)
severity-info-border: hsl(199, 89%, 60%)

# Toggle States
toggle-active-bg: hsl(142, 76%, 40%)
toggle-inactive-bg: hsl(220, 13%, 69%)
```

---

## Implementation Steps

### Step 1: Enhanced RuleCard Component

**File:** `src/components/rules/RuleCard.tsx`

**Design Notes:**
- Severity badge is top-right, color-coded
- Toggle switch is prominent, reflects active state
- Rule type and "applies to" are subordinate info
- Delete confirmation is friendly but clear
- Card has hover state (subtle lift)

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Rule, RuleSeverity } from '@/types/rule'
import { Shield, Trash2, Settings } from 'lucide-react'

interface RuleCardProps {
  rule: Rule
  onToggle: (ruleId: string) => void
  onEdit: (rule: Rule) => void
  onDelete: (ruleId: string) => void
}

export const RuleCard = ({ rule, onToggle, onEdit, onDelete }: RuleCardProps) => {
  const getSeverityStyle = (severity: RuleSeverity) => {
    switch (severity) {
      case RuleSeverity.ERROR:
        return {
          variant: 'destructive' as const,
          bg: 'bg-red-50',
          border: 'border-red-200',
        }
      case RuleSeverity.WARNING:
        return {
          variant: 'secondary' as const,
          bg: 'bg-amber-50',
          border: 'border-amber-200',
        }
      case RuleSeverity.INFO:
        return {
          variant: 'outline' as const,
          bg: 'bg-blue-50',
          border: 'border-blue-200',
        }
      default:
        return {
          variant: 'default' as const,
          bg: 'bg-muted',
          border: 'border-border',
        }
    }
  }

  const severityStyle = getSeverityStyle(rule.severity)

  return (
    <Card className="group transition-all duration-200 hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start gap-4">
          {/* Rule Icon */}
          <div className={`p-2 rounded-lg ${severityStyle.bg} ${severityStyle.border} border-2`}>
            <Shield className="h-5 w-5" aria-hidden="true" />
          </div>

          {/* Title & Description */}
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg leading-snug mb-1">{rule.name}</CardTitle>
            <p className="text-sm text-muted-foreground line-clamp-2">{rule.description}</p>
          </div>

          {/* Severity Badge - Top Right */}
          <Badge variant={severityStyle.variant} className="shrink-0">
            {rule.severity}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Metadata - Subordinate */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <div className="text-xs text-muted-foreground mb-0.5">Type</div>
            <div className="font-medium">{rule.rule_type.replace(/_/g, ' ')}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-0.5">Applies To</div>
            <div className="font-medium capitalize">{rule.applies_to}</div>
          </div>
        </div>

        {/* Status Toggle - Prominent */}
        <div className="flex items-center justify-between py-3 px-4 rounded-lg bg-muted/50 border">
          <Label
            htmlFor={`toggle-${rule.rule_id}`}
            className="flex items-center gap-2 cursor-pointer"
          >
            <span className="font-medium">Status</span>
            <span className={rule.is_active ? 'text-green-600' : 'text-muted-foreground'}>
              {rule.is_active ? 'Active' : 'Inactive'}
            </span>
          </Label>
          <Switch
            id={`toggle-${rule.rule_id}`}
            checked={rule.is_active}
            onCheckedChange={() => onToggle(rule.rule_id)}
            aria-label={`Toggle ${rule.name} ${rule.is_active ? 'inactive' : 'active'}`}
          />
        </div>

        {/* Actions - Secondary */}
        <div className="flex gap-2 pt-2 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onEdit(rule)}
            className="flex-1 gap-1.5"
          >
            <Settings className="h-3.5 w-3.5" aria-hidden="true" />
            Edit
          </Button>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm" className="flex-1 gap-1.5 text-red-600 hover:bg-red-50">
                <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                Delete
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Rule?</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to delete <strong>{rule.name}</strong>?
                  <br />
                  This rule will be marked as inactive and teams will no longer be validated against it.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => onDelete(rule.rule_id)}
                  className="bg-red-600 hover:bg-red-700"
                >
                  Delete Rule
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </CardContent>
    </Card>
  )
}
```

### Step 2: Enhanced RulesAdmin Page

**File:** `src/pages/RulesAdmin.tsx`

**Design Notes:**
- Page header: title + create button (clear hierarchy)
- Filters are compact, visually subordinate
- Rule count shown after filters (helpful context)
- Grid is consistent (2 columns desktop, 1 mobile)
- Empty state is helpful, not just "no results"

```typescript
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { RuleCard } from '@/components/rules/RuleCard'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { EmptyState } from '@/components/common/EmptyState'
import { useToast } from '@/components/ui/use-toast'
import { rulesApi } from '@/api/rules'
import { Rule, RuleType } from '@/types/rule'
import { PlusCircle, Shield, Filter } from 'lucide-react'

export default function RulesAdmin() {
  const { toast } = useToast()
  const [rules, setRules] = useState<Rule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [ruleTypeFilter, setRuleTypeFilter] = useState<RuleType | 'all'>('all')
  const [activeFilter, setActiveFilter] = useState<boolean | 'all'>('all')

  const fetchRules = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await rulesApi.getAll()
      setRules(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load rules')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRules()
  }, [])

  const handleToggle = async (ruleId: string) => {
    try {
      await rulesApi.toggle(ruleId)
      toast({
        title: 'Rule updated',
        description: 'Status changed successfully',
      })
      fetchRules()
    } catch (err: any) {
      toast({
        title: 'Failed to update rule',
        description: err.response?.data?.detail || 'Something went wrong',
        variant: 'destructive',
      })
    }
  }

  const handleEdit = (rule: Rule) => {
    toast({
      title: 'Edit Rule',
      description: 'Edit functionality coming soon',
    })
    console.log('Edit rule:', rule)
  }

  const handleDelete = async (ruleId: string) => {
    try {
      await rulesApi.delete(ruleId)
      toast({
        title: 'Rule deleted',
        description: 'Rule has been marked as inactive',
      })
      fetchRules()
    } catch (err: any) {
      toast({
        title: 'Failed to delete rule',
        description: err.response?.data?.detail || 'Something went wrong',
        variant: 'destructive',
      })
    }
  }

  // Filter rules
  const filteredRules = rules.filter((rule) => {
    const matchesType = ruleTypeFilter === 'all' || rule.rule_type === ruleTypeFilter
    const matchesActive = activeFilter === 'all' || rule.is_active === activeFilter
    return matchesType && matchesActive
  })

  // Loading State
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-64 bg-muted animate-pulse rounded" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-64 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  // Error State
  if (error) {
    return <ErrorDisplay message={error} onRetry={fetchRules} />
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Rules Management</h1>
          <p className="text-muted-foreground mt-1">
            Configure validation rules for fantasy teams
          </p>
        </div>
        <Button size="lg" className="gap-2">
          <PlusCircle className="h-5 w-5" aria-hidden="true" />
          Create Rule
        </Button>
      </div>

      {/* Filters - Compact, Subordinate */}
      <div className="flex flex-wrap items-center gap-3 p-4 bg-muted/30 rounded-lg border">
        <Filter className="h-4 w-4 text-muted-foreground" aria-hidden="true" />

        <Select
          value={ruleTypeFilter}
          onValueChange={(v) => setRuleTypeFilter(v as RuleType | 'all')}
        >
          <SelectTrigger className="w-48 bg-background">
            <SelectValue placeholder="Rule Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value={RuleType.BUDGET_CAP}>Budget Cap</SelectItem>
            <SelectItem value={RuleType.ROSTER_SIZE}>Roster Size</SelectItem>
            <SelectItem value={RuleType.DRS_BOOST_REQUIRED}>DRS Boost Required</SelectItem>
            <SelectItem value={RuleType.MAX_TEAMS_PER_USER}>Max Teams Per User</SelectItem>
            <SelectItem value={RuleType.TRANSFER_LIMIT}>Transfer Limit</SelectItem>
            <SelectItem value={RuleType.DRIVER_ELIGIBILITY}>Driver Eligibility</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={activeFilter === 'all' ? 'all' : activeFilter.toString()}
          onValueChange={(v) => {
            if (v === 'all') setActiveFilter('all')
            else setActiveFilter(v === 'true')
          }}
        >
          <SelectTrigger className="w-40 bg-background">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Rules</SelectItem>
            <SelectItem value="true">Active Only</SelectItem>
            <SelectItem value="false">Inactive Only</SelectItem>
          </SelectContent>
        </Select>

        {/* Rule Count - Helpful Context */}
        {filteredRules.length > 0 && (
          <Badge variant="secondary" className="ml-auto px-3 py-1.5">
            {filteredRules.length} {filteredRules.length === 1 ? 'rule' : 'rules'}
          </Badge>
        )}
      </div>

      {/* Rules Grid or Empty State */}
      {filteredRules.length === 0 ? (
        <EmptyState
          icon={Shield}
          title="No rules found"
          description={
            ruleTypeFilter !== 'all' || activeFilter !== 'all'
              ? "No rules match your current filters. Try adjusting the filters above."
              : "No validation rules have been created yet."
          }
          action={
            (ruleTypeFilter !== 'all' || activeFilter !== 'all') ? (
              <Button
                variant="outline"
                onClick={() => {
                  setRuleTypeFilter('all')
                  setActiveFilter('all')
                }}
              >
                Clear Filters
              </Button>
            ) : (
              <Button size="lg" className="gap-2">
                <PlusCircle className="h-5 w-5" />
                Create First Rule
              </Button>
            )
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredRules.map((rule) => (
            <RuleCard
              key={rule.rule_id}
              rule={rule}
              onToggle={handleToggle}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  )
}
```

### Step 3: Enhanced EmptyState Component (if not already created)

Already created in Dashboard refinement. Reuse the same component.

---

## Design Testing Checklist

### Visual Hierarchy
- [ ] Rule name is most prominent
- [ ] Severity badge is unmissable (color + position)
- [ ] Toggle switch is clearly the primary action
- [ ] Metadata is subordinate but scannable

### Status Clarity
- [ ] Active rules have green "Active" label + toggle ON
- [ ] Inactive rules have gray "Inactive" label + toggle OFF
- [ ] Toggle state transitions smoothly (animation)
- [ ] Card styling reflects active/inactive (subtle difference)

### Severity Design
- [ ] Error badge is red
- [ ] Warning badge is amber
- [ ] Info badge is blue
- [ ] Icon background matches badge color

### Interaction Design
- [ ] Cards lift on hover (subtle shadow increase)
- [ ] Toggle switch is large enough (touch-friendly)
- [ ] Delete confirmation is clear and friendly
- [ ] Edit button is obviously secondary to toggle

### Filters
- [ ] Filters are compact, not dominating
- [ ] Filter changes update grid instantly
- [ ] Rule count updates with filters
- [ ] "Clear Filters" button appears in empty state when filtered

### Responsive Design
- [ ] Mobile: Single column, cards stack beautifully
- [ ] Desktop: 2 columns, consistent gaps
- [ ] Filters wrap on mobile
- [ ] No horizontal scroll at any viewport

### Accessibility
- [ ] Toggle switch has proper label
- [ ] Keyboard navigation works (Tab, Enter, Esc)
- [ ] Screen reader announces status changes
- [ ] Delete confirmation is keyboard accessible

---

## Acceptance Criteria

✅ **Feature is design-complete when:**

1. Rule cards are scannable at a glance
2. Active/inactive status is unmistakable
3. Severity colors are clear and semantic
4. Toggle interaction feels immediate
5. Delete confirmation is friendly but clear
6. Filters work intuitively
7. Empty state is helpful, not just "no data"
8. Responsive layout works on all devices
9. Accessibility passes keyboard + screen reader tests
10. Design feels premium, not "admin interface ugly"

**The Jobs Test:**
- Can an admin scan all rules in < 10 seconds? → YES
- Is toggling a rule obvious? → YES
- Does this feel as polished as the user-facing screens? → YES

---

## Definition of Done

- [ ] All design testing checklist items pass
- [ ] Toggle updates instantly (< 200ms response)
- [ ] Delete confirmation tested
- [ ] Filters tested with all combinations
- [ ] Empty state tested (no rules, filtered no results)
- [ ] No TypeScript errors
- [ ] DESIGN_SYSTEM.md tokens used exclusively
- [ ] Accessibility tested
- [ ] Screenshots captured
- [ ] LESSONS.md updated

**All frontend features complete! Ready for final polish and testing.**
