import { DEFAULT_API_BASE_URL } from '../constants'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL

export class ApiError extends Error {
  readonly status: number
  readonly detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
}

export async function request<T>(
  path: string,
  { method = 'GET', body }: RequestOptions = {},
): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    // fetch rejects only on network/CORS failure, never on HTTP error codes.
    throw new ApiError(0, 'Cannot reach the API. Is the backend running?')
  }

  if (!response.ok) {
    throw new ApiError(response.status, await readDetail(response))
  }

  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

async function readDetail(response: Response): Promise<string> {
  try {
    const { detail } = (await response.json()) as { detail?: unknown }
    if (typeof detail === 'string') return detail
    // FastAPI validation errors are a list of per-field problems.
    if (Array.isArray(detail)) {
      return detail
        .map((item) => (item as { msg?: string }).msg ?? 'invalid input')
        .join('; ')
    }
  } catch {
    // Non-JSON body (proxy or gateway error) — fall through to the generic message.
  }
  return `Request failed with status ${response.status}`
}
