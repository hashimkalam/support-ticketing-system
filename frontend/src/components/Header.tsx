import { useAgent } from '../context/AgentContext'

export default function Header() {
  const { email, hasValidEmail, setEmail } = useAgent()

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl flex-col gap-4 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">
            Support Tickets
          </h1>
          <p className="text-sm text-slate-500">
            Claim tickets from the shared queue.
          </p>
        </div>

        <div className="sm:w-80">
          <label
            htmlFor="agent-email"
            className="block text-xs font-medium text-slate-600"
          >
            Working as
          </label>
          <input
            id="agent-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@company.com"
            autoComplete="email"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 shadow-sm outline-none placeholder:text-slate-400 focus:border-slate-900 focus:ring-2 focus:ring-slate-900/10"
          />
          {email.length > 0 && !hasValidEmail && (
            <p className="mt-1 text-xs text-amber-600">
              Enter a valid email address to claim tickets.
            </p>
          )}
        </div>
      </div>
    </header>
  )
}
