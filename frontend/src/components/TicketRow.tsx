import { useState } from 'react'
import type { TicketRowProps } from '../types'
import TicketDetail from './TicketDetail'
import { PriorityBadge, StatusBadge } from './TicketBadges'

export default function TicketRow({
  ticket,
  canClaim,
  isClaiming,
  onClaim,
}: TicketRowProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const isClaimable = ticket.status === 'open' && ticket.assigned_to === null

  return (
    <li className="p-4">
      <div className="flex items-start justify-between gap-4">
        <button
          type="button"
          onClick={() => setIsExpanded((expanded) => !expanded)}
          aria-expanded={isExpanded}
          className="flex-1 cursor-pointer text-left"
        >
          <span className="flex flex-wrap items-center gap-2">
            <PriorityBadge priority={ticket.priority} />
            <StatusBadge status={ticket.status} />
            <span className="font-medium text-slate-900">{ticket.title}</span>
          </span>
          <span className="mt-1 block text-xs text-slate-500">
            {ticket.assigned_to
              ? `Assigned to ${ticket.assigned_to}`
              : 'Unassigned'}
            {' · opened '}
            {new Date(ticket.created_at).toLocaleDateString()}
          </span>
        </button>

        {isClaimable && (
          <button
            type="button"
            onClick={() => onClaim(ticket)}
            disabled={!canClaim || isClaiming}
            title={
              canClaim ? undefined : 'Add your email in the header to claim tickets'
            }
            className="shrink-0 cursor-pointer rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {isClaiming ? 'Claiming…' : 'Claim'}
          </button>
        )}
      </div>

      {isExpanded && <TicketDetail ticket={ticket} />}
    </li>
  )
}
