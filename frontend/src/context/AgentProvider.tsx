import { useMemo, useState } from 'react'
import { AGENT_STORAGE_KEY } from '../constants'
import type { AgentContextValue, AgentProviderProps } from '../types'
import { AgentContext, isValidEmail } from './AgentContext'

export default function AgentProvider({ children }: AgentProviderProps) {
  // Lazy initialiser so the signed-in agent survives a refresh.
  const [email, setEmail] = useState(
    () => localStorage.getItem(AGENT_STORAGE_KEY) ?? '',
  )

  const value = useMemo<AgentContextValue>(
    () => ({
      email,
      hasValidEmail: isValidEmail(email),
      // Written here rather than in an effect so storage always matches state.
      setEmail: (next: string) => {
        localStorage.setItem(AGENT_STORAGE_KEY, next)
        setEmail(next)
      },
    }),
    [email],
  )

  return <AgentContext.Provider value={value}>{children}</AgentContext.Provider>
}
