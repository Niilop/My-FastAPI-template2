import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router'
import { apiRequest, errorMessage } from '../api/client'
import type { Token, User } from '../api/types'
import { useAuth } from '../auth/context'

export function AuthPage({ register = false }: { register?: boolean }) {
  const { session, signIn } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  const from: unknown = location.state?.from
  const destination = typeof from === 'string' && ['/items', '/account'].includes(from) ? from : '/'

  if (session) return <Navigate to={destination} replace />

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const identifier = String(form.get('identifier') || '')
    const password = String(form.get('password') || '')
    setPending(true)
    setError('')
    try {
      if (register) {
        await apiRequest<User>('/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: identifier, username: form.get('username'), password }),
        })
        navigate('/login', { replace: true, state: { from: destination, registered: true } })
        return
      }
      const token = await apiRequest<Token>('/auth/login', {
        method: 'POST',
        body: new URLSearchParams({ username: identifier, password }),
      })
      const user = await apiRequest<User>('/auth/me', { token: token.access_token })
      signIn({ token: token.access_token, user })
      navigate(destination, { replace: true })
    } catch (error) {
      setError(errorMessage(error))
    } finally {
      setPending(false)
    }
  }

  return (
    <section className="auth-page">
      <p className="eyebrow">Your account</p>
      <h1>{register ? 'Create an account' : 'Welcome back'}</h1>
      <p className="muted">
        {register
          ? 'Get started with your own workspace.'
          : 'Sign in to access your items and account.'}
      </p>
      {!register && location.state?.registered && (
        <p className="notice success" role="status">
          Account created. You can now sign in.
        </p>
      )}
      <form className="panel" onSubmit={submit}>
        <label htmlFor="identifier">{register ? 'Email' : 'Email or username'}</label>
        <input
          id="identifier"
          name="identifier"
          type={register ? 'email' : 'text'}
          autoComplete={register ? 'email' : 'username'}
          required
          maxLength={255}
        />
        {register && (
          <>
            <label htmlFor="username">Username</label>
            <input
              id="username"
              name="username"
              autoComplete="username"
              required
              minLength={3}
              maxLength={100}
              pattern="[a-zA-Z0-9_.\-]+"
              aria-describedby="username-hint"
            />
            <small id="username-hint">3–100 letters, numbers, dots, underscores, or hyphens.</small>
          </>
        )}
        <label htmlFor="password">Password</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete={register ? 'new-password' : 'current-password'}
          required
          minLength={register ? 12 : undefined}
          maxLength={128}
          aria-describedby={register ? 'password-hint' : undefined}
        />
        {register && <small id="password-hint">Use 12–128 characters.</small>}
        {error && (
          <p className="notice error" role="alert">
            {error}
          </p>
        )}
        <button disabled={pending}>
          {pending ? 'Please wait…' : register ? 'Create account' : 'Sign in'}
        </button>
      </form>
      <p className="auth-switch">
        {register ? 'Already have an account? ' : 'New to the workspace? '}
        <Link to={register ? '/login' : '/register'} state={{ from: destination }}>
          {register ? 'Sign in' : 'Create an account'}
        </Link>
      </p>
    </section>
  )
}
