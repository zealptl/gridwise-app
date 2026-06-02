import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { RuleCard } from '@/components/rules/RuleCard'
import { RuleFormDialog } from '@/components/rules/RuleFormDialog'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { EmptyState } from '@/components/common/EmptyState'
import { useToast } from '@/hooks/use-toast'
import { rulesApi } from '@/api/rules'
import type { Rule, RuleType, RuleCreate, RuleUpdate } from '@/types/rule'
import { PlusCircle, Shield, Filter } from 'lucide-react'

export default function RulesAdmin() {
  const { toast } = useToast()
  const [rules, setRules] = useState<Rule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<Rule | null>(null)

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
    setEditingRule(rule)
    setDialogOpen(true)
  }

  const handleCreate = () => {
    setEditingRule(null)
    setDialogOpen(true)
  }

  const handleFormSubmit = async (data: RuleCreate | RuleUpdate) => {
    try {
      if (editingRule) {
        await rulesApi.update(editingRule.rule_id, data as RuleUpdate)
        toast({ title: 'Rule updated', description: 'Changes saved successfully' })
      } else {
        await rulesApi.create(data as RuleCreate)
        toast({ title: 'Rule created', description: 'New rule added successfully' })
      }
      fetchRules()
    } catch (err: any) {
      toast({
        title: editingRule ? 'Failed to update rule' : 'Failed to create rule',
        description: err.response?.data?.detail || 'Something went wrong',
        variant: 'destructive',
      })
      throw err
    }
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
        <Button size="lg" className="gap-2" onClick={handleCreate}>
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
            <SelectItem value="budget_cap">Budget Cap</SelectItem>
            <SelectItem value="roster_size">Roster Size</SelectItem>
            <SelectItem value="drs_boost_required">DRS Boost Required</SelectItem>
            <SelectItem value="max_teams_per_user">Max Teams Per User</SelectItem>
            <SelectItem value="transfer_limit">Transfer Limit</SelectItem>
            <SelectItem value="driver_eligibility">Driver Eligibility</SelectItem>
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

      <RuleFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        rule={editingRule}
        onSubmit={handleFormSubmit}
      />

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
              <Button size="lg" className="gap-2" onClick={handleCreate}>
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
