import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Constructor } from '@/types/constructor'
import { Building2, Check } from 'lucide-react'

interface ConstructorSelectorProps {
  constructors: Constructor[]
  selectedConstructors: Constructor[]
  onSelectionChange: (constructors: Constructor[]) => void
  maxSelection?: number
}

export const ConstructorSelector = ({
  constructors,
  selectedConstructors,
  onSelectionChange,
  maxSelection = 2,
}: ConstructorSelectorProps) => {
  const handleToggle = (constructor: Constructor) => {
    const isSelected = selectedConstructors.some((c) => c.constructor_id === constructor.constructor_id)

    if (isSelected) {
      onSelectionChange(selectedConstructors.filter((c) => c.constructor_id !== constructor.constructor_id))
    } else if (selectedConstructors.length < maxSelection) {
      onSelectionChange([...selectedConstructors, constructor])
    }
  }

  const selectionComplete = selectedConstructors.length === maxSelection

  return (
    <Card className={`transition-all duration-300 ${selectionComplete ? 'ring-2 ring-green-200' : ''}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Building2 className="h-5 w-5 text-primary" aria-hidden="true" />
            Select Constructors
          </CardTitle>
          <Badge
            variant={selectionComplete ? 'default' : 'secondary'}
            className="text-base px-3 py-1 transition-all duration-300"
          >
            {selectedConstructors.length} / {maxSelection}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-2">
          {constructors
            .filter((c) => c.status === 'active')
            .map((constructor) => {
              const isSelected = selectedConstructors.some((c) => c.constructor_id === constructor.constructor_id)
              const canSelect = selectedConstructors.length < maxSelection || isSelected
              const isDisabled = !canSelect

              return (
                <div
                  key={constructor.constructor_id}
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
                  onClick={() => canSelect && handleToggle(constructor)}
                  onKeyDown={(e) => { if ((e.key === 'Enter' || e.key === ' ') && canSelect) { e.preventDefault(); handleToggle(constructor) } }}
                  aria-pressed={isSelected}
                  aria-disabled={isDisabled}
                  aria-label={`${constructor.name}, ${constructor.price}M${isSelected ? ', selected' : ''}${isDisabled ? ', cannot select more constructors' : ''}`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      aria-hidden="true"
                      className={`h-4 w-4 shrink-0 rounded-sm border border-primary flex items-center justify-center transition-colors duration-150 ${isSelected ? 'bg-primary text-primary-foreground' : ''} ${isDisabled ? 'opacity-50' : ''}`}
                    >
                      {isSelected && <Check className="h-3 w-3" />}
                    </div>
                    <div className="text-left">
                      <div className="font-medium">{constructor.name}</div>
                      <div className="text-sm text-muted-foreground">{constructor.full_name}</div>
                    </div>
                  </div>
                  <div className="font-bold text-lg tabular-nums">{constructor.price.toFixed(1)}M</div>
                </div>
              )
            })}
        </div>

        {/* Helper Text - Contextual */}
        <div className="mt-4">
          {selectedConstructors.length === 0 && (
            <p className="text-sm text-muted-foreground text-center">
              Select {maxSelection} constructors to continue
            </p>
          )}
          {selectedConstructors.length > 0 && selectedConstructors.length < maxSelection && (
            <p className="text-sm text-muted-foreground text-center">
              Select {maxSelection - selectedConstructors.length} more constructor{maxSelection - selectedConstructors.length !== 1 ? 's' : ''}
            </p>
          )}
          {selectionComplete && (
            <p className="text-sm text-green-700 font-medium text-center bg-green-50 rounded-md px-3 py-2 animate-in fade-in duration-300">
              Constructor selection complete ✓
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
