import { useMemo } from 'react'
import type { Driver } from '@/types/driver'
import type { Constructor } from '@/types/constructor'

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
