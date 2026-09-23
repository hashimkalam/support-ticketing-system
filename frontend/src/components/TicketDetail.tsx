import type { TicketDetailProps } from '../types'
import { PriorityBadge, StatusBadge } from './TicketBadges'

const labelClass =
  'text-xs font-semibold uppercase tracking-wide text-slate-500'

export default function TicketDetail({ ticket }: TicketDetailProps) {
  return (
    <div className="mt-4 space-y-4 rounded-lg bg-slate-50 p-4 ring-1 ring-slate-200">
      <section>
        <h3 className={labelClass}>Description</h3>
        <p className="mt-1 text-sm whitespace-pre-wrap text-slate-700">
          {ticket.description}
        </p>
      </section>

      <div className="grid gap-4 sm:grid-cols-3">
        <section>
          <h3 className={labelClass}>Status</h3>
          <div className="mt-1">
            <StatusBadge status={ticket.status} />
          </div>
        </section>
        <section>
          <h3 className={labelClass}>Priority</h3>
          <div className="mt-1">
            <PriorityBadge priority={ticket.priority} />
          </div>
        </section>
        <section>
          <h3 className={labelClass}>Assignee</h3>
          <p className="mt-1 text-sm text-slate-700">
            {ticket.assigned_to ?? 'Unassigned'}
          </p>
        </section>
      </div>

      <section>
        <h3 className={labelClass}>Tags</h3>
        {ticket.tags.length === 0 ? (
          <p className="mt-1 text-sm text-slate-500">No tags</p>
        ) : (
          <ul className="mt-1 flex flex-wrap gap-2">
            {ticket.tags.map((tag) => (
              <li
                key={tag}
                className="rounded-full bg-slate-200 px-2.5 py-0.5 text-xs font-medium text-slate-700"
              >
                {tag}
              </li>
            ))}
          </ul>
        )}
      </section>

      <dl className="grid gap-1 border-t border-slate-200 pt-3 text-xs text-slate-500 sm:grid-cols-2">
        <div>
          <dt className="inline font-medium">Ticket ID: </dt>
          <dd className="inline font-mono">{ticket.id}</dd>
        </div>
        <div>
          <dt className="inline font-medium">Opened: </dt>
          <dd className="inline">{new Date(ticket.created_at).toLocaleString()}</dd>
        </div>
        <div>
          <dt className="inline font-medium">Last updated: </dt>
          <dd className="inline">{new Date(ticket.updated_at).toLocaleString()}</dd>
        </div>
      </dl>
    </div>
  )
}
