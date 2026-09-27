import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { errorMessage } from '../api/client'
import type { Item, ItemList } from '../api/types'
import { useAuth } from '../auth/context'

const pageSize = 20

export function ItemsPage() {
  const { request } = useAuth()
  const [page, setPage] = useState<ItemList>({ items: [], total: 0 })
  const [offset, setOffset] = useState(0)
  const [revision, setRevision] = useState(0)
  const [loading, setLoading] = useState(true)
  const [pending, setPending] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    const { signal } = controller
    void request<ItemList>(`/items?limit=${pageSize}&offset=${offset}`, { signal })
      .then((data) => {
        if (!signal.aborted) {
          setPage(data)
          setLoadError('')
        }
      })
      .catch((error: unknown) => {
        if (!signal.aborted) setLoadError(errorMessage(error))
      })
      .finally(() => {
        if (!signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [request, offset, revision])

  function reload(nextOffset = offset) {
    setLoading(true)
    setLoadError('')
    setOffset(nextOffset)
    setRevision((value) => value + 1)
  }

  function edit(item: Item | null) {
    setEditingId(item?.id ?? null)
    setTitle(item?.title ?? '')
    setDescription(item?.description ?? '')
    setDeletingId(null)
    setError('')
    setNotice('')
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setPending(true)
    setError('')
    setNotice('')
    try {
      await request<Item>(editingId === null ? '/items' : `/items/${editingId}`, {
        method: editingId === null ? 'POST' : 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description }),
      })
      edit(null)
      setNotice(editingId === null ? 'Item created.' : 'Item updated.')
      reload(editingId === null ? 0 : offset)
    } catch (error) {
      setError(errorMessage(error))
    } finally {
      setPending(false)
    }
  }

  async function remove(id: number) {
    setPending(true)
    setError('')
    setNotice('')
    try {
      await request<void>(`/items/${id}`, { method: 'DELETE' })
      if (editingId === id) edit(null)
      setDeletingId(null)
      setNotice('Item deleted.')
      reload(page.items.length === 1 ? Math.max(0, offset - pageSize) : offset)
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
        <h1>Items</h1>
        <p>Keep a title and a few details. Only you can see your items.</p>
      </div>
      <section className="panel" aria-labelledby="item-heading">
        <h2 id="item-heading">{editingId === null ? 'Add an item' : 'Edit item'}</h2>
        <form onSubmit={save}>
          <label htmlFor="item-title">Title</label>
          <input
            id="item-title"
            required
            maxLength={255}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            disabled={pending}
          />
          <label htmlFor="item-description">
            Description <span className="muted">(optional)</span>
          </label>
          <textarea
            id="item-description"
            rows={3}
            maxLength={5000}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            disabled={pending}
          />
          <div className="form-actions">
            <button disabled={pending || !title.trim()}>
              {pending ? 'Saving…' : editingId === null ? 'Create item' : 'Save changes'}
            </button>
            {editingId !== null && (
              <button
                type="button"
                className="secondary"
                disabled={pending}
                onClick={() => edit(null)}
              >
                Cancel edit
              </button>
            )}
          </div>
        </form>
      </section>
      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="notice success" role="status">
          {notice}
        </p>
      )}
      <section className="item-list" aria-labelledby="items-heading" aria-busy={loading}>
        <div className="section-heading">
          <h2 id="items-heading">Your items</h2>
          <button
            className="secondary small"
            disabled={loading || pending}
            onClick={() => reload()}
          >
            Refresh
          </button>
        </div>
        {loadError ? (
          <p className="notice error" role="alert">
            {loadError}
          </p>
        ) : loading ? (
          <p>Loading items…</p>
        ) : page.items.length === 0 ? (
          <div className="empty-state">
            <h3>No items here</h3>
            <p>Create an item using the form above.</p>
          </div>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Added</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {page.items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <strong>{item.title}</strong>
                      {item.description && (
                        <span className="table-description">{item.description}</span>
                      )}
                    </td>
                    <td>{new Date(item.created_at).toLocaleDateString()}</td>
                    <td>
                      <div className="item-actions">
                        {deletingId === item.id ? (
                          <>
                            <span>Delete this item?</span>
                            <button
                              className="small"
                              disabled={pending}
                              onClick={() => void remove(item.id)}
                            >
                              Confirm delete
                            </button>
                            <button
                              className="secondary small"
                              disabled={pending}
                              onClick={() => setDeletingId(null)}
                            >
                              Cancel delete
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              className="secondary small"
                              disabled={pending}
                              aria-label={`Edit ${item.title}`}
                              onClick={() => {
                                edit(item)
                                document.getElementById('item-title')?.focus()
                              }}
                            >
                              Edit
                            </button>
                            <button
                              className="secondary small"
                              disabled={pending}
                              aria-label={`Delete ${item.title}`}
                              onClick={() => setDeletingId(item.id)}
                            >
                              Delete
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="form-actions" aria-label="Pagination">
          <button
            className="secondary small"
            disabled={loading || pending || offset === 0}
            onClick={() => reload(Math.max(0, offset - pageSize))}
          >
            Previous
          </button>
          <button
            className="secondary small"
            disabled={loading || pending || offset + pageSize >= page.total}
            onClick={() => reload(offset + pageSize)}
          >
            Next
          </button>
          {!loading && !loadError && (
            <span className="muted">
              {page.total} items · Page {offset / pageSize + 1}
            </span>
          )}
        </div>
      </section>
    </>
  )
}
