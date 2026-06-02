import type { LucideIcon } from 'lucide-react'

interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description?: string
  action?: React.ReactNode
}

export const EmptyState = ({
  icon: Icon,
  title,
  description,
  action
}: EmptyStateProps) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {Icon && (
        <div className="mb-6 rounded-full bg-muted p-6">
          <Icon className="h-12 w-12 text-muted-foreground" aria-hidden="true" />
        </div>
      )}
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      {description && (
        <p className="text-base text-muted-foreground max-w-md mb-6">
          {description}
        </p>
      )}
      {action}
    </div>
  )
}
