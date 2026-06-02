import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import type { Driver } from '@/types/driver'
import { Zap } from 'lucide-react'

interface DrsBoostSelectorProps {
  selectedDrivers: Driver[]
  drsBoostDriverId: string | null
  onDrsBoostChange: (driverId: string) => void
}

export const DrsBoostSelector = ({
  selectedDrivers,
  drsBoostDriverId,
  onDrsBoostChange,
}: DrsBoostSelectorProps) => {
  if (selectedDrivers.length === 0) {
    return (
      <Card className="opacity-50">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Zap className="h-5 w-5" aria-hidden="true" />
            DRS Boost
          </CardTitle>
          <CardDescription>
            Select drivers first to assign DRS Boost
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const isComplete = drsBoostDriverId !== null

  return (
    <Card className={`transition-all duration-300 ${isComplete ? 'ring-2 ring-yellow-200' : ''}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Zap className="h-5 w-5 text-yellow-600" aria-hidden="true" />
          DRS Boost
          {isComplete && <span className="text-green-600 text-sm font-normal">✓</span>}
        </CardTitle>
        <CardDescription>
          Choose one driver to boost with DRS
        </CardDescription>
      </CardHeader>

      <CardContent>
        <div className="space-y-2" role="radiogroup">
          {selectedDrivers.map((driver) => {
            const isChecked = drsBoostDriverId === driver.driver_id
            return (
              <div
                key={driver.driver_id}
                className={`
                  flex items-center space-x-3 rounded-lg border-2 p-3 transition-all duration-200 cursor-pointer
                  ${isChecked
                    ? 'border-yellow-400 bg-yellow-50 scale-[1.02] shadow-sm'
                    : 'border-border hover:bg-muted hover:scale-[1.01]'
                  }
                `}
              >
                <input
                  type="radio"
                  id={`drs-${driver.driver_id}`}
                  name="drs-boost"
                  value={driver.driver_id}
                  checked={isChecked}
                  onChange={() => onDrsBoostChange(driver.driver_id)}
                  className="h-4 w-4 border border-primary text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
                <Label
                  htmlFor={`drs-${driver.driver_id}`}
                  className="flex-1 cursor-pointer font-medium"
                >
                  {driver.first_name} {driver.last_name}
                </Label>
                {isChecked && (
                  <Zap className="h-4 w-4 text-yellow-600 fill-yellow-600 animate-pulse" aria-hidden="true" />
                )}
              </div>
            )
          })}
        </div>

        {isComplete && (
          <p className="mt-4 text-sm text-green-700 font-medium text-center bg-green-50 rounded-md px-3 py-2 animate-in fade-in duration-300">
            DRS Boost assigned ✓
          </p>
        )}
      </CardContent>
    </Card>
  )
}
