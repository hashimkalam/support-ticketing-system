import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError } from '../api/client'
import { fetchTickets } from '../api/tickets'
import type { Ticket, TicketListResponse, UseTicketsResult } from '../types'

export function useTickets(limit: number): UseTicketsResult {
  const [page, setPage] = useState(0)
  const [data, setData] = useState<TicketListResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const latestRequest = useRef(0)

  const skip = page * limit

  const fetchPage = useCallback(async () => {
    const requestId = ++latestRequest.current
    try {
      const response = await fetchTickets({ skip, limit })
      // Rapid paging can resolve out of order; only the newest response lands.
      if (requestId !== latestRequest.current) return
      setData(response)
      setError(null)
    } catch (cause) {
      if (requestId !== latestRequest.current) return
      setError(cause instanceof ApiError ? cause.detail : 'Could not load tickets.')
    } finally {
      if (requestId === latestRequest.current) setIsLoading(false)
    }
  }, [skip, limit])

  useEffect(() => {
    // Fetching on mount is the point of the hook; the rule assumes a state-only
    // effect. Replacing this needs a data library, which the MVP does without.
    // oxlint-disable-next-line react/set-state-in-effect
    void fetchPage()
  }, [fetchPage])

  // Loading is flipped by the event that starts a request, never inside the
  // effect, so mounting a page never triggers an extra render pass.
  const goToPage = useCallback((next: number) => {
    setIsLoading(true)
    setPage(next)
  }, [])

  const reload = useCallback(() => {
    setIsLoading(true)
    void fetchPage()
  }, [fetchPage])

  const replaceTicket = useCallback((updated: Ticket) => {
    setData((current) =>
      current === null
        ? current
        : {
            ...current,
            items: current.items.map((ticket) =>
              ticket.id === updated.id ? updated : ticket,
            ),
          },
    )
  }, [])

  const totalCount = data?.total_count ?? 0
  const returned = data?.items.length ?? 0

  return {
    tickets: data?.items ?? [],
    totalCount,
    page,
    pageCount: Math.max(1, Math.ceil(totalCount / limit)),
    rangeStart: totalCount === 0 ? 0 : skip + 1,
    rangeEnd: skip + returned,
    isLoading,
    error,
    canGoNext: skip + limit < totalCount,
    canGoPrevious: page > 0,
    goToNextPage: () => goToPage(page + 1),
    goToPreviousPage: () => goToPage(Math.max(0, page - 1)),
    reload,
    replaceTicket,
  }
}
