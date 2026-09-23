import type { TicketListProps } from '../types'
import TicketRow from './TicketRow'

export default function TicketList({
  tickets,
  isLoading,
  error,
  claimingId,
  canClaim,
  onClaim,
  onRetry,
}: TicketListProps) {
  if (error) {
    return (
      <div
        role="alert"
        className="flex items-center justify-between gap-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
      >
        <span>{error}</span>
        <button
          type="button"
          onClick={onRetry}
          className="shrink-0 cursor-pointer rounded-lg bg-red-600 px-3 py-1.5 font-medium text-white hover:bg-red-700"
        >
          Try again
        </button>
      </div>
    )
  }

  if (isLoading && tickets.length === 0) {
    return (
      <p className="rounded-xl border border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-500">
        Loading tickets…
      </p>
    )
  }

  if (tickets.length === 0) {
    return (
      <p className="rounded-xl border border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-500">
        No tickets on this page.
      </p>
    )
  }

  return (
    <ul className="divide-y divide-slate-200 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      {tickets.map((ticket) => (
        <TicketRow
          key={ticket.id}
          ticket={ticket}
          canClaim={canClaim}
          isClaiming={claimingId === ticket.id}
          onClaim={onClaim}
        />
      ))}
    </ul>
  )
}
