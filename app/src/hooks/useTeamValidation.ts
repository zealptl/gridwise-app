import { useMemo } from 'react'
import type { Driver } from '@/types/driver'
import type { Constructor } from '@/types/constructor'

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
