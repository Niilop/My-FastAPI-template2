import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router'
import { apiRequest, errorMessage } from '../api/client'
import type { ExampleResult } from '../api/types'
import { useAuth } from '../auth/context'

export function OverviewPage() {
  const { session } = useAuth()
  const [result, setResult] = useState('')
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setPending(true)
    setError('')
    setResult('')
    try {
      const data = await apiRequest<ExampleResult>('/example/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: form.get('name'), task: form.get('task') }),
      })
      setResult(data.result)
    } catch (error) {
      setError(errorMessage(error))
    } finally {
      setPending(false)
    }
  }

  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">Your workspace</p>
        <h1>{session ? `Welcome, ${session.user.username}.` : 'A place to start.'}</h1>
        <p>Manage your account, save an item, or try a simple request.</p>
      </div>
      <div className="overview-grid">
        <section className="panel">
          <h2>Try a request</h2>
          <p className="muted">Send a name and a task to the example endpoint.</p>
          <form onSubmit={submit}>
            <label htmlFor="example-name">Name</label>
            <input
              id="example-name"
              name="name"
              required
              maxLength={100}
              defaultValue="Developer"
            />
            <label htmlFor="example-task">Task</label>
            <input
              id="example-task"
              name="task"
              required
              maxLength={1000}
              defaultValue="Test the connection"
            />
            {error && (
              <p className="notice error" role="alert">
                {error}
              </p>
            )}
            {result && (
              <p className="notice success" role="status">
                {result}
              </p>
            )}
            <button disabled={pending}>{pending ? 'Sending…' : 'Send request'}</button>
          </form>
        </section>
        <aside className="overview-aside">
          <p className="eyebrow">Start here</p>
          <h2>Save something useful.</h2>
          <p>
            Keep a note or an idea with a title and description. You can edit or delete it later.
          </p>
          <Link className="text-link" to="/items">
            Open items <span aria-hidden="true">→</span>
          </Link>
          <hr />
          <p className="muted">
            {session
              ? 'Your account is ready. Build your next feature from here.'
              : 'New here? Create an account to save your first item.'}
          </p>
          {!session && (
            <Link className="text-link" to="/register">
              Create an account <span aria-hidden="true">→</span>
            </Link>
          )}
        </aside>
      </div>
    </>
  )
}
