import { useEffect } from 'react'
import { TOAST_DURATION_MS } from '../constants'
import type { ToastProps } from '../types'

export default function Toast({ toast, onDismiss }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, TOAST_DURATION_MS)
    return () => clearTimeout(timer)
    // Keyed on the message so a new alert restarts the countdown.
  }, [toast, onDismiss])

  const isError = toast.kind === 'error'

  return (
    <div className="pointer-events-none fixed inset-x-0 top-4 z-50 flex justify-center px-4">
      <div
        role={isError ? 'alert' : 'status'}
        className={`pointer-events-auto flex w-full max-w-md items-start gap-3 rounded-lg px-4 py-3 text-sm shadow-lg ${
          isError ? 'bg-red-600 text-white' : 'bg-slate-900 text-white'
        }`}
      >
        <p className="flex-1">{toast.message}</p>
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss notification"
          className="cursor-pointer text-white/70 hover:text-white"
        >
          ✕
        </button>
      </div>
    </div>
  )
}
