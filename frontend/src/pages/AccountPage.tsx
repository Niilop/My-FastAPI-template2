import { useAuth } from '../auth/context'

export function AccountPage() {
  const { session } = useAuth()
  if (!session) return null
  const { user } = session
  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">Personal details</p>
        <h1>Your account</h1>
        <p>The details associated with your workspace.</p>
      </div>
      <section className="panel account-details" aria-label="Account details">
        <dl>
          <div>
            <dt>Username</dt>
            <dd>{user.username}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{user.email}</dd>
          </div>
          <div>
            <dt>Member since</dt>
            <dd>{new Date(user.created_at).toLocaleDateString()}</dd>
          </div>
        </dl>
      </section>
    </>
  )
}
