export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

type RequestOptions = RequestInit & { token?: string }

function errorDetail(payload: unknown): string | undefined {
  if (!payload || typeof payload !== 'object' || !('detail' in payload)) return
  const detail = payload.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const messages = detail.flatMap((issue: unknown) => {
      if (!issue || typeof issue !== 'object' || !('msg' in issue)) return []
      return typeof issue.msg === 'string' ? [issue.msg] : []
    })
    return messages.length ? messages.join('. ') : undefined
  }
}

export async function apiRequest<T>(
  path: string,
  { token, headers, signal, ...options }: RequestOptions = {},
): Promise<T> {
  const requestHeaders = new Headers(headers)
  if (token) requestHeaders.set('Authorization', `Bearer ${token}`)
  let response: Response
  try {
    const timeout = AbortSignal.timeout(30_000)
    response = await fetch(`/api${path}`, {
      ...options,
      headers: requestHeaders,
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    })
  } catch (error) {
    if (signal?.aborted) throw error
    throw new Error(
      error instanceof Error && error.name === 'TimeoutError'
        ? 'The request timed out. Please try again.'
        : 'Cannot reach the server. Please try again.',
      { cause: error },
    )
  }
  const payload: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(
      response.status,
      errorDetail(payload) || `Request failed (${response.status}). Please try again.`,
    )
  }
  if (payload === null && response.status !== 204) {
    throw new Error('The server returned an unexpected response.')
  }
  return payload as T
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.'
}
