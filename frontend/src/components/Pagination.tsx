import type { PaginationProps } from '../types'

const buttonClass =
  'cursor-pointer rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-white'

export default function Pagination({
  page,
  pageCount,
  totalCount,
  rangeStart,
  rangeEnd,
  isLoading,
  canGoNext,
  canGoPrevious,
  onNext,
  onPrevious,
}: PaginationProps) {
  return (
    <nav
      aria-label="Ticket pagination"
      className="mt-4 flex flex-wrap items-center justify-between gap-3"
    >
      <p className="text-sm text-slate-500">
        {totalCount === 0
          ? 'No tickets to show'
          : `Showing ${rangeStart}–${rangeEnd} of ${totalCount}`}
        <span className="ml-2 text-slate-400">
          Page {page + 1} of {pageCount}
        </span>
      </p>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onPrevious}
          disabled={!canGoPrevious || isLoading}
          className={buttonClass}
        >
          ← Previous
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={!canGoNext || isLoading}
          className={buttonClass}
        >
          Next →
        </button>
      </div>
    </nav>
  )
}
