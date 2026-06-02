import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'

interface ValidationErrorsProps {
  errors: string[]
}

export const ValidationErrors = ({ errors }: ValidationErrorsProps) => {
  if (errors.length === 0) return null

  return (
    <Alert variant="destructive" className="animate-in fade-in slide-in-from-top-2 duration-300">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle className="font-semibold">Please complete the following:</AlertTitle>
      <AlertDescription>
        <ul className="list-disc list-inside mt-2 space-y-1 text-sm">
          {errors.map((error, index) => (
            <li key={index}>{error}</li>
          ))}
        </ul>
      </AlertDescription>
    </Alert>
  )
}
