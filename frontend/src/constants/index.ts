import type { Status } from '../types'

export const AGENT_STORAGE_KEY = 'support-ticketing.agent-email'

export const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export const DEFAULT_API_BASE_URL = 'http://localhost:8000/api/v1'

export const DEFAULT_PAGE_SIZE = 10

export const DEFAULT_FETCH_LIMIT = 20

export const TOAST_DURATION_MS = 6000

export const STATUS_LABELS: Record<Status, string> = {
  open: 'Open',
  in_progress: 'In progress',
  resolved: 'Resolved',
}
