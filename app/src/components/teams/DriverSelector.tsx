import { useState, useMemo, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { Driver } from '@/types/driver'
import { Search, X, Users, Check } from 'lucide-react'

interface DriverSelectorProps {
  drivers: Driver[]
  selectedDrivers: Driver[]
  onSelectionChange: (drivers: Driver[]) => void
  maxSelection?: number
}

export const DriverSelector = ({
  drivers,
  selectedDrivers,
  onSelectionChange,
  maxSelection = 5,
}: DriverSelectorProps) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [teamFilter, setTeamFilter] = useState<string | null>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  const filteredDrivers = useMemo(() => {
    return drivers.filter((driver) => {
      const matchesSearch =
        driver.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        driver.last_name.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesTeam = !teamFilter || driver.team_name === teamFilter
      return matchesSearch && matchesTeam && driver.status === 'active'
    })
  }, [drivers, searchTerm, teamFilter])

  const teams = useMemo(() => {
    return Array.from(new Set(drivers.map((d) => d.team_name).filter(Boolean))).sort()
  }, [drivers])

  const handleToggle = (driver: Driver) => {
    const isSelected = selectedDrivers.some((d) => d.driver_id === driver.driver_id)

    if (isSelected) {
      onSelectionChange(selectedDrivers.filter((d) => d.driver_id !== driver.driver_id))
    } else if (selectedDrivers.length < maxSelection) {
      onSelectionChange([...selectedDrivers, driver])
    }
  }

  const clearSearch = () => {
    setSearchTerm('')
    searchInputRef.current?.focus()
  }

  const selectionComplete = selectedDrivers.length === maxSelection

  return (
    <Card className={`transition-all duration-300 ${selectionComplete ? 'ring-2 ring-green-200' : ''}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Users className="h-5 w-5 text-primary" aria-hidden="true" />
            Select Drivers
          </CardTitle>
          <Badge
            variant={selectionComplete ? 'default' : 'secondary'}
            className="text-base px-3 py-1 transition-all duration-300"
          >
            {selectedDrivers.length} / {maxSelection}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Search Input - Focus First */}
        <div className="relative">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none"
            aria-hidden="true"
          />
          <Input
            ref={searchInputRef}
            placeholder="Search by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9 pr-9"
            aria-label="Search drivers"
          />
          {searchTerm && (
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0 hover:bg-muted"
              onClick={clearSearch}
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Team Filter Pills - Touch Friendly */}
        <div className="flex flex-wrap gap-2">
          <Badge
            variant={teamFilter === null ? 'default' : 'outline'}
            className="cursor-pointer px-3 py-1.5 transition-all duration-200 hover:scale-105"
            onClick={() => setTeamFilter(null)}
          >
            All Teams
          </Badge>
          {teams.map((team) => (
            <Badge
              key={team}
              variant={teamFilter === team ? 'default' : 'outline'}
              className="cursor-pointer px-3 py-1.5 transition-all duration-200 hover:scale-105"
              onClick={() => setTeamFilter(team)}
            >
              {team}
            </Badge>
          ))}
        </div>

        {/* Driver List - Scrollable with Clear Selection States */}
        <div className="h-[400px] overflow-y-auto -mr-4 pr-4">
          <div className="space-y-2">
            {filteredDrivers.length === 0 ? (
              <div className="text-center py-8 text-sm text-muted-foreground">
                No drivers found
              </div>
            ) : (
              filteredDrivers.map((driver) => {
                const isSelected = selectedDrivers.some((d) => d.driver_id === driver.driver_id)
                const canSelect = selectedDrivers.length < maxSelection || isSelected
                const isDisabled = !canSelect

                return (
                  <div
                    key={driver.driver_id}
                    role="button"
                    tabIndex={isDisabled ? -1 : 0}
                    className={`
                      w-full flex items-center justify-between p-3 rounded-lg border-2 transition-all duration-200
                      ${isSelected
                        ? 'bg-primary/5 border-primary shadow-sm scale-[1.02]'
                        : 'border-border hover:bg-muted hover:border-muted-foreground/20 hover:scale-[1.01]'
                      }
                      ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
                    `}
                    onClick={() => canSelect && handleToggle(driver)}
                    onKeyDown={(e) => { if ((e.key === 'Enter' || e.key === ' ') && canSelect) { e.preventDefault(); handleToggle(driver) } }}
                    aria-pressed={isSelected}
                    aria-disabled={isDisabled}
                    aria-label={`${driver.first_name} ${driver.last_name}, ${driver.team_name}, ${driver.price}M${isSelected ? ', selected' : ''}${isDisabled ? ', cannot select more drivers' : ''}`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        aria-hidden="true"
                        className={`h-4 w-4 shrink-0 rounded-sm border border-primary flex items-center justify-center transition-colors duration-150 ${isSelected ? 'bg-primary text-primary-foreground' : ''} ${isDisabled ? 'opacity-50' : ''}`}
                      >
                        {isSelected && <Check className="h-3 w-3" />}
                      </div>
                      <div className="text-left">
                        <div className="font-medium">
                          {driver.first_name} {driver.last_name}
                        </div>
                        <div className="text-sm text-muted-foreground">{driver.team_name}</div>
                      </div>
                    </div>
                    <div className="font-bold text-lg tabular-nums">{driver.price.toFixed(1)}M</div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* Helper Text - Contextual */}
        {selectedDrivers.length === 0 && (
          <p className="text-sm text-muted-foreground text-center">
            Select {maxSelection} drivers to continue
          </p>
        )}
        {selectedDrivers.length > 0 && selectedDrivers.length < maxSelection && (
          <p className="text-sm text-muted-foreground text-center">
            Select {maxSelection - selectedDrivers.length} more {maxSelection - selectedDrivers.length === 1 ? 'driver' : 'drivers'}
          </p>
        )}
        {selectionComplete && (
          <p className="text-sm text-green-700 font-medium text-center bg-green-50 rounded-md px-3 py-2 animate-in fade-in duration-300">
            Driver selection complete ✓
          </p>
        )}
      </CardContent>
    </Card>
  )
}
