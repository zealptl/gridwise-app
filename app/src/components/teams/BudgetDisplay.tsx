import { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle, CheckCircle, Wallet } from 'lucide-react'

interface BudgetDisplayProps {
  budgetUsed: number
  budgetRemaining: number
  budgetCap: number
  isOverBudget: boolean
}

export const BudgetDisplay = ({
  budgetUsed,
  budgetRemaining,
  budgetCap,
  isOverBudget,
}: BudgetDisplayProps) => {
  const percentage = (budgetUsed / budgetCap) * 100

  // Semantic color based on budget status
  const statusColor = useMemo(() => {
    if (isOverBudget) return 'text-red-600'
    if (percentage > 90) return 'text-amber-600'
    return 'text-green-600'
  }, [isOverBudget, percentage])

  const progressColor = useMemo(() => {
    if (isOverBudget) return 'bg-red-600'
    if (percentage > 90) return 'bg-amber-600'
    return 'bg-green-600'
  }, [isOverBudget, percentage])

  const ringColor = useMemo(() => {
    if (isOverBudget) return 'ring-red-200'
    if (percentage === 100) return 'ring-green-200'
    return ''
  }, [isOverBudget, percentage])

  return (
    <Card className={`sticky top-6 transition-all duration-300 ${ringColor ? `ring-2 ${ringColor}` : ''}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Wallet className="h-5 w-5 text-primary" aria-hidden="true" />
          Budget
          {isOverBudget ? (
            <AlertCircle className="h-4 w-4 text-red-600 animate-pulse" aria-label="Over budget" />
          ) : percentage === 100 ? (
            <CheckCircle className="h-4 w-4 text-green-600" aria-label="Budget maximized" />
          ) : null}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Large Number Display - Primary Hierarchy */}
        <div className="space-y-1">
          <div className="flex items-baseline justify-between">
            <span className="text-sm text-muted-foreground font-medium">Used</span>
            <span className={`text-2xl font-bold tabular-nums ${statusColor} transition-colors duration-200`}>
              {budgetUsed.toFixed(1)}M
            </span>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-sm text-muted-foreground font-medium">Remaining</span>
            <span className={`text-lg font-semibold tabular-nums ${isOverBudget ? 'text-red-600' : 'text-muted-foreground'} transition-colors duration-200`}>
              {budgetRemaining.toFixed(1)}M
            </span>
          </div>
        </div>

        {/* Visual Progress - Animated */}
        <div className="space-y-2">
          <div className="relative h-3 w-full overflow-hidden rounded-full bg-muted">
            <div
              className={`h-full ${progressColor} transition-all duration-300 ease-out`}
              style={{ width: `${Math.min(percentage, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground tabular-nums">
            <span>0M</span>
            <span>{budgetCap}M</span>
          </div>
        </div>

        {/* Status Message - Contextual */}
        {isOverBudget && (
          <div className="text-sm text-red-600 font-medium bg-red-50 rounded-md px-3 py-2 animate-in fade-in slide-in-from-top-2 duration-200">
            Over budget by {Math.abs(budgetRemaining).toFixed(1)}M
          </div>
        )}

        {!isOverBudget && percentage > 95 && percentage < 100 && (
          <div className="text-sm text-amber-700 font-medium bg-amber-50 rounded-md px-3 py-2">
            Almost at budget cap
          </div>
        )}

        {!isOverBudget && budgetUsed === 0 && (
          <div className="text-sm text-muted-foreground bg-muted rounded-md px-3 py-2">
            Select players to see budget usage
          </div>
        )}

        {!isOverBudget && percentage === 100 && (
          <div className="text-sm text-green-700 font-medium bg-green-50 rounded-md px-3 py-2">
            Budget perfectly optimized ✓
          </div>
        )}
      </CardContent>
    </Card>
  )
}
