import { createContext, useContext } from 'react'
import type { User } from '../api/types'

export interface Session {
  token: string
  user: User
}

interface AuthContextValue {
  session: Session | null
  signIn: (session: Session) => void
  signOut: () => void
  request: <T>(path: string, options?: RequestInit) => Promise<T>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth requires AuthProvider')
  return value
}
