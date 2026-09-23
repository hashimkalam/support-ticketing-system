import type { Ticket } from './tickets'

export interface AgentContextValue {
  email: string
  hasValidEmail: boolean
  setEmail: (email: string) => void
}

export interface UseTicketsResult {
  tickets: Ticket[]
  totalCount: number
  page: number
  pageCount: number
  rangeStart: number
  rangeEnd: number
  isLoading: boolean
  error: string | null
  canGoNext: boolean
  canGoPrevious: boolean
  goToNextPage: () => void
  goToPreviousPage: () => void
  reload: () => void
  replaceTicket: (updated: Ticket) => void
}
