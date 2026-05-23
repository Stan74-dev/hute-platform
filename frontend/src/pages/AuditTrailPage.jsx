import { useEffect, useState } from 'react'
import API from '../api/client'

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

export default function AuditTrailPage() {
  const [logs, setLogs] = useState([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadLogs = async (searchValue = '') => {
    try {
      setLoading(true)
      setError('')

      const url = searchValue
        ? `/accounts/audit-logs/?q=${encodeURIComponent(searchValue)}`
        : '/accounts/audit-logs/'

      const { data } = await API.get(url)
      setLogs(Array.isArray(data) ? data : [])
    } catch (err) {
      const data = err.response?.data
      if (typeof data === 'string') {
        setError(data)
      } else if (data?.detail) {
        setError(data.detail)
      } else {
        setError('Could not load audit logs.')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadLogs()
  }, [])

  return (
    <div>
      <div className="section-header">
        <h2>Audit Trail</h2>
        <p className="muted-text">
          Review who did what, when, and against which record.
        </p>
      </div>

      <div className="content-card" style={{ marginTop: '18px' }}>
        <label>Search Audit Logs</label>
        <div style={{ display: 'flex', gap: '10px', marginTop: '10px', flexWrap: 'wrap' }}>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by actor, action, or description"
          />
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => loadLogs(query)}
          >
            Search
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              setQuery('')
              loadLogs('')
            }}
          >
            Reset
          </button>
        </div>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading audit logs...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Audit Events</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Target Type</th>
                <th>Target ID</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{formatDate(log.created_at)}</td>
                  <td>{log.actor_username}</td>
                  <td>{log.action}</td>
                  <td>{log.target_type || '-'}</td>
                  <td>{log.target_id || '-'}</td>
                  <td>{log.description || '-'}</td>
                </tr>
              ))}
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="6">No audit logs found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}