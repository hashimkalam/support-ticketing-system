import type { ReactNode } from 'react'
import type { Priority, Status, Ticket } from './tickets'

export interface ToastProps {
  toast: ToastMessage
  onDismiss: () => void
}

export type ToastKind = 'success' | 'error'

export interface ToastMessage {
  kind: ToastKind
  message: string
}

export interface PriorityBadgeProps {
  priority: Priority
}

export interface StatusBadgeProps {
  status: Status
}

export interface TicketListProps {
  tickets: Ticket[]
  isLoading: boolean
  error: string | null
  claimingId: string | null
  canClaim: boolean
  onClaim: (ticket: Ticket) => void
  onRetry: () => void
}

export interface TicketRowProps {
  ticket: Ticket
  canClaim: boolean
  isClaiming: boolean
  onClaim: (ticket: Ticket) => void
}

export interface TicketDetailProps {
  ticket: Ticket
}

export interface PaginationProps {
  page: number
  pageCount: number
  totalCount: number
  rangeStart: number
  rangeEnd: number
  isLoading: boolean
  canGoNext: boolean
  canGoPrevious: boolean
  onNext: () => void
  onPrevious: () => void
}

export interface AgentProviderProps {
  children: ReactNode
}
