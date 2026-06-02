import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import type { Rule } from '@/types/rule'
import { Shield, Trash2, Settings } from 'lucide-react'

interface RuleCardProps {
  rule: Rule
  onToggle: (ruleId: string) => void
  onEdit: (rule: Rule) => void
  onDelete: (ruleId: string) => void
}

export const RuleCard = ({ rule, onToggle, onEdit, onDelete }: RuleCardProps) => {
  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'error':
        return {
          variant: 'destructive' as const,
          bg: 'bg-red-50',
          border: 'border-red-200',
          iconBg: 'bg-red-50 border-red-200',
        }
      case 'warning':
        return {
          variant: 'secondary' as const,
          bg: 'bg-amber-50',
          border: 'border-amber-200',
          iconBg: 'bg-amber-50 border-amber-200',
        }
      case 'info':
        return {
          variant: 'outline' as const,
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          iconBg: 'bg-blue-50 border-blue-200',
        }
      default:
        return {
          variant: 'default' as const,
          bg: 'bg-muted',
          border: 'border-border',
          iconBg: 'bg-muted border-border',
        }
    }
  }

  const severityStyle = getSeverityStyle(rule.severity)

  // Format rule type for display
  const formatRuleType = (ruleType: string) => {
    return ruleType.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
  }

  return (
    <Card className="group transition-all duration-200 hover:shadow-md hover:-translate-y-0.5">
      <CardHeader className="pb-3">
        <div className="flex items-start gap-4">
          {/* Rule Icon */}
          <div className={`p-2 rounded-lg ${severityStyle.iconBg} border-2`}>
            <Shield className="h-5 w-5" aria-hidden="true" />
          </div>

          {/* Title & Description */}
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg leading-snug mb-1">{rule.name}</CardTitle>
            <p className="text-sm text-muted-foreground line-clamp-2">{rule.description}</p>
          </div>

          {/* Severity Badge - Top Right */}
          <Badge variant={severityStyle.variant} className="shrink-0">
            {rule.severity.toUpperCase()}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Metadata - Subordinate */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <div className="text-xs text-muted-foreground mb-0.5">Type</div>
            <div className="font-medium">{formatRuleType(rule.rule_type)}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground mb-0.5">Applies To</div>
            <div className="font-medium capitalize">{rule.applies_to}</div>
          </div>
        </div>

        {/* Status Toggle - Prominent */}
        <div className="flex items-center justify-between py-3 px-4 rounded-lg bg-muted/50 border">
          <Label
            htmlFor={`toggle-${rule.rule_id}`}
            className="flex items-center gap-2 cursor-pointer"
          >
            <span className="font-medium">Status</span>
            <span className={rule.is_active ? 'text-green-600' : 'text-muted-foreground'}>
              {rule.is_active ? 'Active' : 'Inactive'}
            </span>
          </Label>
          <Switch
            id={`toggle-${rule.rule_id}`}
            checked={rule.is_active}
            onCheckedChange={() => onToggle(rule.rule_id)}
            aria-label={`Toggle ${rule.name} ${rule.is_active ? 'inactive' : 'active'}`}
          />
        </div>

        {/* Actions - Secondary */}
        <div className="flex gap-2 pt-2 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onEdit(rule)}
            className="flex-1 gap-1.5"
          >
            <Settings className="h-3.5 w-3.5" aria-hidden="true" />
            Edit
          </Button>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm" className="flex-1 gap-1.5 text-red-600 hover:bg-red-50">
                <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                Delete
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Rule?</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to delete <strong>{rule.name}</strong>?
                  <br />
                  This rule will be marked as inactive and teams will no longer be validated against it.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => onDelete(rule.rule_id)}
                  className="bg-red-600 hover:bg-red-700"
                >
                  Delete Rule
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </CardContent>
    </Card>
  )
}
