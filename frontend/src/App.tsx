import { useCallback, useState } from 'react'
import { ApiError } from './api/client'
import { claimTicket } from './api/tickets'
import Header from './components/Header'
import Pagination from './components/Pagination'
import TicketList from './components/TicketList'
import Toast from './components/Toast'
import { DEFAULT_PAGE_SIZE } from './constants'
import { useAgent } from './context/AgentContext'
import AgentProvider from './context/AgentProvider'
import { useTickets } from './hooks/useTickets'
import type { Ticket, ToastMessage } from './types'

function TicketWorkspace() {
  const { email, hasValidEmail } = useAgent()
  const {
    tickets,
    totalCount,
    page,
    pageCount,
    rangeStart,
    rangeEnd,
    isLoading,
    error,
    canGoNext,
    canGoPrevious,
    goToNextPage,
    goToPreviousPage,
    reload,
    replaceTicket,
  } = useTickets(DEFAULT_PAGE_SIZE)

  const [claimingId, setClaimingId] = useState<string | null>(null)
  const [toast, setToast] = useState<ToastMessage | null>(null)

  const dismissToast = useCallback(() => setToast(null), [])

  async function handleClaim(ticket: Ticket) {
    setClaimingId(ticket.id)
    try {
      const result = await claimTicket(ticket.id, email.trim())

      switch (result.outcome) {
        case 'claimed':
          // The API returns the updated row, so no refetch is needed.
          replaceTicket(result.ticket)
          setToast({
            kind: 'success',
            message: `“${result.ticket.title}” is now assigned to you.`,
          })
          break

        case 'conflict':
          setToast({ kind: 'error', message: result.message })
          // Fire and forget: losing the race means our snapshot is stale, but the
          // alert shouldn't wait on the refetch to render.
          void reload()
          break
      }
    } catch (cause) {
      setToast({
        kind: 'error',
        message:
          cause instanceof ApiError ? cause.detail : 'Could not claim this ticket.',
      })
    } finally {
      setClaimingId(null)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Header />

      <main className="mx-auto max-w-5xl px-6 py-8">
        <div className="mb-4">
          <h2 className="text-base font-semibold">Ticket queue</h2>
          <p className="text-sm text-slate-500">
            {isLoading && tickets.length === 0
              ? 'Loading…'
              : `${totalCount} ticket${totalCount === 1 ? '' : 's'} total`}
          </p>
        </div>

        <TicketList
          tickets={tickets}
          isLoading={isLoading}
          error={error}
          claimingId={claimingId}
          canClaim={hasValidEmail}
          onClaim={handleClaim}
          onRetry={reload}
        />

        <Pagination
          page={page}
          pageCount={pageCount}
          totalCount={totalCount}
          rangeStart={rangeStart}
          rangeEnd={rangeEnd}
          isLoading={isLoading}
          canGoNext={canGoNext}
          canGoPrevious={canGoPrevious}
          onNext={goToNextPage}
          onPrevious={goToPreviousPage}
        />
      </main>

      {toast && <Toast toast={toast} onDismiss={dismissToast} />}
    </div>
  )
}

export default function App() {
  return (
    <AgentProvider>
      <TicketWorkspace />
    </AgentProvider>
  )
}
