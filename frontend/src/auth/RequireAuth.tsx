import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from './context'

export function RequireAuth() {
  const { session } = useAuth()
  const location = useLocation()
  if (!session) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }
  return <Outlet />
}
