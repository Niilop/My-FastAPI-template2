import { useCallback, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { ApiError, apiRequest } from '../api/client'
import { AuthContext } from './context'
import type { Session } from './context'

export function AuthProvider({ children }: { children: ReactNode }) {
  // Keep bearer tokens in memory. Reloading the page starts a new session.
  const [session, setSession] = useState<Session | null>(null)
  const signOut = useCallback(() => setSession(null), [])
  const request = useCallback(
    async <T,>(path: string, options?: RequestInit): Promise<T> => {
      if (!session) throw new ApiError(401, 'Please sign in to continue.')
      try {
        return await apiRequest<T>(path, { ...options, token: session.token })
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          setSession((current) => (current?.token === session.token ? null : current))
        }
        throw error
      }
    },
    [session],
  )
  const value = useMemo(
    () => ({ session, signIn: setSession, signOut, request }),
    [session, signOut, request],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
