import { Link, Route, Routes } from 'react-router'
import { RequireAuth } from './auth/RequireAuth'
import { Layout } from './components/Layout'
import { AccountPage } from './pages/AccountPage'
import { AuthPage } from './pages/AuthPage'
import { ItemsPage } from './pages/ItemsPage'
import { OverviewPage } from './pages/OverviewPage'

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<OverviewPage />} />
        <Route path="login" element={<AuthPage key="login" />} />
        <Route path="register" element={<AuthPage key="register" register />} />
        <Route element={<RequireAuth />}>
          <Route path="account" element={<AccountPage />} />
          <Route path="items" element={<ItemsPage />} />
        </Route>
        <Route
          path="*"
          element={
            <div className="page-heading">
              <p className="eyebrow">404</p>
              <h1>Page not found</h1>
              <p>
                This page doesn’t exist. <Link to="/">Return to the overview.</Link>
              </p>
            </div>
          }
        />
      </Route>
    </Routes>
  )
}
