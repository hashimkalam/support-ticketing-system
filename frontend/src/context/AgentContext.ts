import { createContext, useContext } from 'react'
import { EMAIL_PATTERN } from '../constants'
import type { AgentContextValue } from '../types'

export const AgentContext = createContext<AgentContextValue | null>(null)

export function isValidEmail(value: string): boolean {
  return EMAIL_PATTERN.test(value.trim())
}

export function useAgent(): AgentContextValue {
  const context = useContext(AgentContext)
  if (!context) {
    throw new Error('useAgent must be used inside an AgentProvider')
  }
  return context
}
