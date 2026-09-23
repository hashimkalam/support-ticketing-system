import { DEFAULT_FETCH_LIMIT } from '../constants'
import type {
  ClaimResult,
  CreateTicketInput,
  FetchTicketsParams,
  Ticket,
  TicketListResponse,
} from '../types'
import { ApiError, request } from './client'

export async function createTicket(input: CreateTicketInput): Promise<Ticket> {
  return request<Ticket>('/tickets', { method: 'POST', body: input })
}

export async function fetchTickets({
  skip = 0,
  limit = DEFAULT_FETCH_LIMIT,
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
