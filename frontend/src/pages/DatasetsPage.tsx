import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { errorMessage } from '../api/client'
import type { Dataset, DatasetQuota } from '../api/types'
import { useAuth } from '../auth/context'

export function DatasetsPage() {
  const { request } = useAuth()
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [quota, setQuota] = useState<DatasetQuota | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [uploadError, setUploadError] = useState('')
  const [notice, setNotice] = useState('')
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    const { signal } = controller
    void Promise.all([
      request<Dataset[]>('/data/catalog', { signal }),
      request<DatasetQuota>('/data/count', { signal }),
    ])
      .then(([items, limits]) => {
        if (!signal.aborted) {
          setDatasets(items)
          setQuota(limits)
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
  }, [request, revision])

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    setUploading(true)
    setUploadError('')
    setNotice('')
    try {
      await request<Dataset>('/data/upload', { method: 'POST', body: new FormData(form) })
      form.reset()
      setNotice('Dataset uploaded.')
      setRevision((value) => value + 1)
    } catch (error) {
      setUploadError(errorMessage(error))
    } finally {
      setUploading(false)
    }
  }

  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">Your data</p>
        <h1>Datasets</h1>
        <p>Upload CSV files and browse your catalog.</p>
      </div>
      <section className="panel" aria-labelledby="upload-heading">
        <h2 id="upload-heading">Add a dataset</h2>
        <form onSubmit={upload}>
          <div className="form-grid">
            <div>
              <label htmlFor="dataset-name">Name</label>
              <input id="dataset-name" name="name" required maxLength={255} />
            </div>
            <div>
              <label htmlFor="dataset-file">CSV file</label>
              <input id="dataset-file" name="file" type="file" accept=".csv,text/csv" required />
            </div>
          </div>
          <label htmlFor="dataset-description">
            Description <span className="muted">(optional)</span>
          </label>
          <input id="dataset-description" name="description" maxLength={5000} />
          {uploadError && (
            <p className="notice error" role="alert">
              {uploadError}
            </p>
          )}
          {notice && (
            <p className="notice success" role="status">
              {notice}
            </p>
          )}
          <div className="form-actions">
            <button disabled={uploading || quota?.remaining === 0}>
              {uploading ? 'Uploading…' : 'Upload dataset'}
            </button>
            {quota && (
              <span className="muted">
                {quota.count} of {quota.limit} datasets used
              </span>
            )}
          </div>
        </form>
      </section>
      <section className="catalog" aria-labelledby="catalog-heading" aria-busy={loading}>
        <div className="section-heading">
          <h2 id="catalog-heading">Your catalog</h2>
          <button
            className="button secondary small"
            onClick={() => setRevision((value) => value + 1)}
          >
            Refresh
          </button>
        </div>
        {loadError ? (
          <p className="notice error" role="alert">
            {loadError}
          </p>
        ) : loading ? (
          <p role="status">Loading datasets…</p>
        ) : datasets.length === 0 ? (
          <div className="empty-state">
            <h3>No datasets yet</h3>
            <p>Your uploaded files will appear here.</p>
          </div>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Rows</th>
                  <th>Columns</th>
                  <th>Added</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((dataset) => (
                  <tr key={dataset.id}>
                    <td>
                      <strong>{dataset.name}</strong>
                      {dataset.description && (
                        <span className="table-description">{dataset.description}</span>
                      )}
                      <details>
                        <summary>Column details</summary>
                        <ul>
                          {dataset.data_metadata.columns.map((column) => (
                            <li key={column}>
                              {column}: {dataset.data_metadata.missing_values[column]} empty values
                            </li>
                          ))}
                        </ul>
                      </details>
                    </td>
                    <td>{dataset.data_metadata.num_rows.toLocaleString()}</td>
                    <td>{dataset.data_metadata.num_cols}</td>
                    <td>{new Date(dataset.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )
}
