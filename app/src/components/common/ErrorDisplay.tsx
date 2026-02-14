import { AlertCircle } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

interface ErrorDisplayProps {
  title?: string
  message: string
  onRetry?: () => void
}

export const ErrorDisplay = ({
  title = 'Error',
  message,
  onRetry
}: ErrorDisplayProps) => {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>
        {message}
        {onRetry && (
          <button
            onClick={onRetry}
            className="ml-2 underline"
          >
            Try again
          </button>
        )}
      </AlertDescription>
    </Alert>
  )
}
