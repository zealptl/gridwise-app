# Feature: Rules Administration

## Overview

Build the rules management interface for admins to view, toggle, and manage validation rules.

**Estimated Time:** 2 hours
**Dependencies:** Foundation setup
**Complexity:** Low-Medium

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

---

## Implementation Steps

### Step 1: Create RuleCard Component

**File:** `src/components/rules/RuleCard.tsx`

```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Rule, RuleSeverity } from '@/types/rule'
import { Edit, Trash2 } from 'lucide-react'

interface RuleCardProps {
  rule: Rule
  onToggle: (ruleId: string) => void
  onEdit: (rule: Rule) => void
  onDelete: (ruleId: string) => void
}

export const RuleCard = ({ rule, onToggle, onEdit, onDelete }: RuleCardProps) => {
  const getSeverityVariant = (severity: RuleSeverity) => {
    switch (severity) {
      case RuleSeverity.ERROR:
        return 'destructive' as const
      case RuleSeverity.WARNING:
        return 'secondary' as const
      case RuleSeverity.INFO:
        return 'outline' as const
      default:
        return 'default' as const
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{rule.name}</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">{rule.description}</p>
          </div>
          <div className="flex items-center gap-2 ml-4">
            <Badge variant={getSeverityVariant(rule.severity)}>{rule.severity}</Badge>
            <Switch checked={rule.is_active} onCheckedChange={() => onToggle(rule.rule_id)} />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Type:</span>
            <span className="font-medium">{rule.rule_type}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Applies to:</span>
            <span className="font-medium">{rule.applies_to}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Status:</span>
            <span className={`font-medium ${rule.is_active ? 'text-green-600' : 'text-muted-foreground'}`}>
              {rule.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>

        <div className="mt-4 flex gap-2">
          <Button variant="outline" size="sm" onClick={() => onEdit(rule)}>
            <Edit className="h-3 w-3 mr-1" />
            Edit
          </Button>
          <Button variant="destructive" size="sm" onClick={() => onDelete(rule.rule_id)}>
            <Trash2 className="h-3 w-3 mr-1" />
            Delete
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
```

### Step 2: Update RulesAdmin Page

**File:** `src/pages/RulesAdmin.tsx`

```typescript
import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { RuleCard } from '@/components/rules/RuleCard'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { EmptyState } from '@/components/common/EmptyState'
import { useToast } from '@/components/ui/use-toast'
import { rulesApi } from '@/api/rules'
import { Rule, RuleType } from '@/types/rule'
import { PlusCircle } from 'lucide-react'

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
      toast({ title: 'Success', description: 'Rule status updated' })
      fetchRules()
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err.response?.data?.detail || 'Failed to toggle rule',
        variant: 'destructive',
      })
    }
  }

  const handleEdit = (rule: Rule) => {
    // TODO: Implement edit dialog/modal
    toast({
      title: 'Edit Rule',
      description: 'Edit functionality coming soon',
    })
    console.log('Edit rule:', rule)
  }

  const handleDelete = async (ruleId: string) => {
    if (!confirm('Are you sure you want to delete this rule?')) return

    try {
      await rulesApi.delete(ruleId)
      toast({ title: 'Success', description: 'Rule deleted' })
      fetchRules()
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err.response?.data?.detail || 'Failed to delete rule',
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

  if (loading) {
    return <LoadingSpinner size="lg" className="mt-12" />
  }

  if (error) {
    return <ErrorDisplay message={error} onRetry={fetchRules} />
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Rules Management</h1>
        <Button>
          <PlusCircle className="h-4 w-4 mr-2" />
          Create Rule
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <Select
          value={ruleTypeFilter}
          onValueChange={(v) => setRuleTypeFilter(v as RuleType | 'all')}
        >
          <SelectTrigger className="w-48">
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
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Rules</SelectItem>
            <SelectItem value="true">Active Only</SelectItem>
            <SelectItem value="false">Inactive Only</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Rules Grid */}
      {filteredRules.length === 0 ? (
        <EmptyState
          title="No rules found"
          description="No rules match your current filters"
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

---

## Testing Requirements

### Unit Tests

**Test RuleCard Component:**

Create `src/components/rules/__tests__/RuleCard.test.tsx`:

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { RuleCard } from '../RuleCard'
import { Rule, RuleType, RuleSeverity } from '@/types/rule'

const mockRule: Rule = {
  rule_id: '123',
  rule_type: RuleType.BUDGET_CAP,
  name: 'Budget Cap Rule',
  description: 'Team must not exceed 100M budget',
  config: { max_budget: 100.0 },
  validation_logic: {
    operator: 'lte',
    field: 'budget_used',
    threshold: '100.0',
    error_message_template: 'Budget exceeded',
  },
  severity: RuleSeverity.ERROR,
  is_active: true,
  applies_to: 'team',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  created_by: 'admin',
}

describe('RuleCard', () => {
  const mockOnToggle = jest.fn()
  const mockOnEdit = jest.fn()
  const mockOnDelete = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders rule information correctly', () => {
    render(
      <RuleCard
        rule={mockRule}
        onToggle={mockOnToggle}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    )

    expect(screen.getByText('Budget Cap Rule')).toBeInTheDocument()
    expect(screen.getByText('Team must not exceed 100M budget')).toBeInTheDocument()
    expect(screen.getByText('budget_cap')).toBeInTheDocument()
    expect(screen.getByText('team')).toBeInTheDocument()
  })

  it('shows correct severity badge', () => {
    render(
      <RuleCard
        rule={mockRule}
        onToggle={mockOnToggle}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    )

    expect(screen.getByText('error')).toBeInTheDocument()
  })

  it('calls onToggle when switch is clicked', () => {
    render(
      <RuleCard
        rule={mockRule}
        onToggle={mockOnToggle}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    )

    const switchElement = screen.getByRole('switch')
    fireEvent.click(switchElement)

    expect(mockOnToggle).toHaveBeenCalledWith('123')
  })

  it('calls onEdit when edit button is clicked', () => {
    render(
      <RuleCard
        rule={mockRule}
        onToggle={mockOnToggle}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    )

    const editButton = screen.getByText('Edit')
    fireEvent.click(editButton)

    expect(mockOnEdit).toHaveBeenCalledWith(mockRule)
  })

  it('calls onDelete when delete button is clicked', () => {
    render(
      <RuleCard
        rule={mockRule}
        onToggle={mockOnToggle}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    )

    const deleteButton = screen.getByText('Delete')
    fireEvent.click(deleteButton)

    expect(mockOnDelete).toHaveBeenCalledWith('123')
  })

  it('shows active status correctly', () => {
    render(
      <RuleCard
        rule={mockRule}
        onToggle={mockOnToggle}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    )

    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('shows inactive status for inactive rule', () => {
    const inactiveRule = { ...mockRule, is_active: false }

    render(
      <RuleCard
        rule={inactiveRule}
        onToggle={mockOnToggle}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
      />
    )

    expect(screen.getByText('Inactive')).toBeInTheDocument()
  })
})
```

---

## Manual Testing Checklist

### Display Tests
- [ ] All rules display in grid layout
- [ ] Rule cards show name and description
- [ ] Rule type displays correctly
- [ ] Severity badge shows with correct color (error=red, warning=yellow, info=gray)
- [ ] "Applies to" field displays correctly
- [ ] Active/Inactive status displays correctly
- [ ] Toggle switch reflects active status (on for active, off for inactive)

### Toggle Functionality
- [ ] Clicking toggle switches rule from active to inactive
- [ ] Clicking toggle switches rule from inactive to active
- [ ] Toggle updates in database (verify with page refresh)
- [ ] Success toast appears after toggle
- [ ] Rule list refreshes after toggle

### Filter Tests
- [ ] "All Types" filter shows all rules
- [ ] Selecting specific type filters to that type only
- [ ] "All Rules" status filter shows all rules
- [ ] "Active Only" filter shows only active rules
- [ ] "Inactive Only" filter shows only inactive rules
- [ ] Filters work together (type + status)

### Delete Functionality
- [ ] Clicking delete shows confirmation dialog
- [ ] Clicking "Cancel" on confirmation does nothing
- [ ] Clicking "OK" on confirmation deletes rule
- [ ] Rule disappears from list after delete
- [ ] Success toast appears after delete
- [ ] Delete is soft delete (rule marked inactive, not removed from DB)

### Edit Functionality
- [ ] Clicking "Edit" shows toast (placeholder for future feature)
- [ ] Edit button is clickable

### Error Handling
- [ ] Stop backend → error message displays
- [ ] Error message has "Try again" button
- [ ] Clicking retry loads rules
- [ ] Failed toggle shows error toast
- [ ] Failed delete shows error toast

### Responsive Design
- [ ] Grid shows 1 column on mobile
- [ ] Grid shows 2 columns on desktop
- [ ] Cards stack properly
- [ ] Text wraps appropriately

---

## Acceptance Criteria

✅ **Feature is complete when:**

1. All rules display correctly in cards
2. Toggle switch activates/deactivates rules via API
3. Delete confirmation works and removes rules
4. Filters update the rule list correctly
5. Severity badges display with correct colors
6. All unit tests pass
7. All manual tests pass
8. No TypeScript errors
9. No console errors or warnings
10. Responsive layout works on all screen sizes

---

## Iteration Instructions

**Keep iterating until all tests pass:**

1. **Build incrementally:**
   - RuleCard component → test
   - RulesAdmin page basic → test
   - Add toggle functionality → test
   - Add delete functionality → test
   - Add filters → test

2. **Test each function:**
   - Toggle: Switch ON → verify API call → verify rule updates
   - Toggle: Switch OFF → verify API call → verify rule updates
   - Delete: Click → confirm → verify API call → verify rule removed
   - Filters: Change each filter → verify list updates

3. **Verify with backend:**
   - Toggle should call `PATCH /api/v1/rules/:id/toggle`
   - Delete should call `DELETE /api/v1/rules/:id`
   - Rule list should refresh after each operation

4. **Common Issues:**
   - Toggle not working → check Switch `onCheckedChange` prop
   - Delete confirmation not showing → ensure `confirm()` is called
   - Filters not working → verify filter logic in `filteredRules`
   - Cards not displaying → check that `rules` array has data

5. **Repeat** until all acceptance criteria met

---

## Definition of Done

- [ ] RuleCard component implemented
- [ ] RulesAdmin page implemented
- [ ] Toggle functionality working
- [ ] Delete functionality working
- [ ] Filters working correctly
- [ ] All unit tests passing
- [ ] All manual tests passing
- [ ] No TypeScript errors
- [ ] No linting errors
- [ ] Responsive layout verified
- [ ] Code committed with clear message

---

## Future Enhancements (Out of Scope)

The following features are intentionally left for future implementation:

- **Create Rule Dialog** - Modal form to create new rules
- **Edit Rule Dialog** - Modal form to edit existing rules
- **Rule Configuration Editor** - UI for editing complex rule configs
- **Rule Preview** - Preview how a rule will validate before saving

These can be added in a future iteration once core functionality is stable.

---

**All features complete! Proceed to final testing and polish phase.**
