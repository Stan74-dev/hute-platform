import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import API from '../api/client'

function badgeClass(value) {
  const v = String(value || '').toLowerCase()
  if (v === 'critical') return 'badge badge-danger'
  if (v === 'high') return 'badge badge-warning'
  if (v === 'medium') return 'badge badge-info'
  if (v === 'low') return 'badge badge-success'
  if (v === 'resolved' || v === 'dismissed') return 'badge badge-success'
  if (v === 'open') return 'badge badge-info'
  return 'badge'
}

function parseCases(payload) {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.cases)) return payload.cases
  if (Array.isArray(payload?.results)) return payload.results
  if (Array.isArray(payload?.rows)) return payload.rows
  return []
}

export default function AnomalyCasesPage() {
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [search, setSearch] = useState('')

  const loadCases = async () => {
    try {
      setLoading(true)
      setError('')

      const params = new URLSearchParams()
      if (statusFilter) params.append('status', statusFilter)
      if (priorityFilter) params.append('priority', priorityFilter)
      if (search) params.append('search', search)
      params.append('page', '1')
      params.append('page_size', '100')

      const response = await API.get(`/accounts/anomaly-cases/?${params.toString()}`)
      setCases(parseCases(response.data))
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load anomaly cases.')
      setCases([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCases()

    const interval = setInterval(() => {
      loadCases()
    }, 5000)

    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, priorityFilter])

  const filteredCases = cases.filter((item) => {
    const haystack = [
      item.id,
      item.title,
      item.description,
      item.status,
      item.priority,
      item.severity,
      item.anomaly_type,
      item.type,
    ]
      .join(' ')
      .toLowerCase()

    return haystack.includes(search.toLowerCase())
  })

  return (
    <div>
      <div className="section-header">
        <h2>Anomaly Cases</h2>
        <p className="muted-text">
          Review and manage anomaly investigation cases.
        </p>
      </div>

      <div className="content-card" style={{ marginTop: '18px' }}>
        <h3>Filters</h3>

        <div style={{ display: 'flex', gap: '10px', marginTop: '12px', flexWrap: 'wrap' }}>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
          </select>

          <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}>
            <option value="">All Priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>

          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search cases"
          />

          <button type="button" className="btn btn-secondary" onClick={loadCases}>
            Reload
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              setStatusFilter('')
              setPriorityFilter('')
              setSearch('')
            }}
          >
            Reset
          </button>
        </div>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading anomaly cases...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Case Register</h3>
        <p className="muted-text" style={{ marginTop: '8px' }}>
          Showing {filteredCases.length} case(s). Auto-refreshes every 5 seconds.
        </p>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Assigned</th>
                <th>SLA</th>
                <th>Evidence</th>
                <th>Title</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {filteredCases.map((item, index) => (
                <tr key={item.id || index}>
                  <td>{item.id || '-'}</td>
                  <td>{item.anomaly_type || item.type || '-'}</td>
                  <td>
                    <span className={badgeClass(item.priority || item.severity)}>
                      {item.priority || item.severity || '-'}
                    </span>
                  </td>
                  <td>
                    <span className={badgeClass(item.status)}>
                      {item.status || '-'}
                    </span>
                  </td>
                  <td>{item.assigned_to_username || item.assigned || '-'}</td>
                  <td>{item.sla_breached ? 'Breached' : 'Healthy'}</td>
                  <td>{item.evidence_count || 0}</td>
                  <td>{item.title || '-'}</td>
                  <td>
                    {item.id ? (
                      <Link to={`/anomaly-cases/${item.id}`} className="btn btn-secondary">
                        Open
                      </Link>
                    ) : (
                      '-'
                    )}
                  </td>
                </tr>
              ))}

              {filteredCases.length === 0 ? (
                <tr>
                  <td colSpan="9">No cases found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}