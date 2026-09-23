import { STATUS_LABELS } from '../constants'
import type {
  Priority,
  PriorityBadgeProps,
  Status,
  StatusBadgeProps,
} from '../types'

const priorityStyles: Record<Priority, string> = {
  low: 'bg-slate-100 text-slate-600 ring-slate-200',
  medium: 'bg-sky-50 text-sky-700 ring-sky-200',
  high: 'bg-amber-50 text-amber-700 ring-amber-200',
  urgent: 'bg-red-50 text-red-700 ring-red-200',
}

const statusStyles: Record<Status, string> = {
  open: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  in_progress: 'bg-violet-50 text-violet-700 ring-violet-200',
  resolved: 'bg-slate-100 text-slate-600 ring-slate-200',
}

const badgeBase =
  'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset'

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  return (
    <span className={`${badgeBase} capitalize ${priorityStyles[priority]}`}>
      {priority}
    </span>
  )
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={`${badgeBase} ${statusStyles[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  )
}
