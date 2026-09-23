export type Priority = 'low' | 'medium' | 'high' | 'urgent'
export type Status = 'open' | 'in_progress' | 'resolved'

export interface Ticket {
  id: string
  title: string
  description: string
  priority: Priority
  status: Status
  tags: string[]
  assigned_to: string | null
  created_at: string
  updated_at: string
}

export interface TicketListResponse {
  items: Ticket[]
  total_count: number
  skip: number
  limit: number
}

export interface CreateTicketInput {
  title: string
  description: string
  priority?: Priority
  tags?: string[]
  assigned_to?: string | null
}

export interface FetchTicketsParams {
  skip?: number
  limit?: number
}

export type ClaimResult =
  | { outcome: 'claimed'; ticket: Ticket }
  | { outcome: 'conflict'; message: string }
