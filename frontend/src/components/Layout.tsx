import { NavLink, Outlet } from 'react-router'
import { useAuth } from '../auth/context'

export function Layout() {
  const { session, signOut } = useAuth()
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="site-header">
        <div className="header-inner">
          <NavLink className="brand" to="/" aria-label="Workspace home">
            <span className="brand-mark" aria-hidden="true">
              W
            </span>
            Workspace
          </NavLink>
          <nav aria-label="Main navigation">
            <NavLink to="/" end>
              Overview
            </NavLink>
            <NavLink to="/items">Items</NavLink>
            {session && <NavLink to="/account">Account</NavLink>}
          </nav>
          <div className="session-actions">
            {session ? (
              <button className="button secondary small" onClick={signOut}>
                Sign out
              </button>
            ) : (
              <NavLink className="button small" to="/login">
                Sign in
              </NavLink>
            )}
          </div>
        </div>
      </header>
      <main id="main" tabIndex={-1}>
        <Outlet />
      </main>
      <footer className="site-footer">Workspace · Application template</footer>
    </>
  )
}
