import { ApiError, request } from './client'

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

export async function createTicket(input: CreateTicketInput): Promise<Ticket> {
  return request<Ticket>('/tickets', { method: 'POST', body: input })
}

export async function fetchTickets({
  skip = 0,
  limit = 20,
}: FetchTicketsParams = {}): Promise<TicketListResponse> {
  const query = new URLSearchParams({ skip: String(skip), limit: String(limit) })
  return request<TicketListResponse>(`/tickets?${query}`)
}

export async function claimTicket(
  ticketId: string,
  assignedTo: string,
): Promise<ClaimResult> {
  try {
    const ticket = await request<Ticket>(
      `/tickets/${encodeURIComponent(ticketId)}/claim`,
      { method: 'POST', body: { assigned_to: assignedTo } },
    )
    return { outcome: 'claimed', ticket }
  } catch (error) {
    // A 409 means another agent won the race: expected under load, not a crash.
    // Everything else (404, 422, network) still propagates to the caller.
    if (error instanceof ApiError && error.status === 409) {
      return { outcome: 'conflict', message: error.detail }
    }
    throw error
  }
}
