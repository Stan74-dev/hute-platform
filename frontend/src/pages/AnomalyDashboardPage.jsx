import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import API from '../api/client'

function todayString() {
  return new Date().toISOString().slice(0, 10)
}

function badgeClass(value) {
  const v = String(value || '').toLowerCase()
  if (v === 'critical') return 'badge badge-danger'
  if (v === 'high') return 'badge badge-warning'
  if (v === 'medium') return 'badge badge-info'
  if (v === 'low') return 'badge badge-success'
  return 'badge'
}

function parseRows(payload) {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.anomalies)) return payload.anomalies
  if (Array.isArray(payload?.results)) return payload.results
  if (Array.isArray(payload?.cases)) return payload.cases
  if (Array.isArray(payload?.rows)) return payload.rows
  return []
}

export default function AnomalyDashboardPage() {
  const [selectedDate, setSelectedDate] = useState(todayString())
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [creatingId, setCreatingId] = useState(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const loadDashboard = async (dateValue = selectedDate) => {
    try {
      setLoading(true)
      setError('')

      const response = await API.get(`/accounts/anomaly-dashboard/?date=${dateValue}`)
      setDashboard(response.data || {})
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load anomaly dashboard.')
      setDashboard(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboard(selectedDate)

    const interval = setInterval(() => {
      loadDashboard(selectedDate)
    }, 5000)

    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate])

  const createCaseFromAnomaly = async (anomaly) => {
    try {
      const anomalyId = anomaly.id || anomaly.anomaly_id || anomaly.source_anomaly_id

      setCreatingId(anomalyId)
      setError('')
      setMessage('')

      const payload = {
        title: anomaly.title || 'Anomaly case',
        description: anomaly.description || anomaly.message || '',
        priority: anomaly.priority || anomaly.severity || 'medium',
        severity: anomaly.severity || anomaly.priority || 'medium',
        status: 'open',
        anomaly_type: anomaly.anomaly_type || anomaly.type || anomaly.code || 'general',
        type: anomaly.type || anomaly.anomaly_type || anomaly.code || 'general',
        score: anomaly.score || 0,
        date: selectedDate,
        source_anomaly_id: anomalyId,
        metadata: {
          source: 'anomaly_dashboard',
          source_anomaly_id: anomalyId,
          shift_id: anomaly.shift_id || null,
          original_anomaly: anomaly,
        },
      }

      await API.post('/accounts/anomaly-cases/', payload)

      setMessage(`Case created for anomaly ${anomalyId || ''}.`)
      await loadDashboard(selectedDate)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create anomaly case.')
    } finally {
      setCreatingId(null)
    }
  }

  const summary = dashboard?.summary || {}
  const anomalies = parseRows(dashboard).filter((row) => {
  // Hide stored case rows from the Detected Anomalies table.
  // Cases have created_at/source_anomaly_id; live anomalies usually have detected_date.
  if (row.created_at && row.source_anomaly_id) return false
  if (row.created_at && row.linked_anomaly_id) return false
  return true
})

  return (
    <div>
      <div className="section-header">
        <h2>Anomaly Dashboard</h2>
        <p className="muted-text">
          Monitor operational anomalies and create linked investigation cases.
        </p>
      </div>

      <div className="content-card" style={{ marginTop: '18px' }}>
        <h3>Date Selection</h3>

        <div style={{ display: 'flex', gap: '10px', marginTop: '12px', flexWrap: 'wrap' }}>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />

          <button type="button" className="btn btn-secondary" onClick={() => loadDashboard(selectedDate)}>
            Reload
          </button>
        </div>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading anomaly dashboard...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}
      {message ? <p style={{ color: 'green', marginTop: '16px' }}>{message}</p> : null}

      <div className="stats-grid" style={{ marginTop: '18px' }}>
        <div className="stat-card">
          <span>Total</span>
          <strong>{summary.total_anomalies || summary.total || anomalies.length || 0}</strong>
        </div>
        <div className="stat-card">
          <span>Critical</span>
          <strong>{summary.critical || 0}</strong>
        </div>
        <div className="stat-card">
          <span>High</span>
          <strong>{summary.high || 0}</strong>
        </div>
        <div className="stat-card">
          <span>Medium</span>
          <strong>{summary.medium || 0}</strong>
        </div>
        <div className="stat-card">
          <span>Low</span>
          <strong>{summary.low || 0}</strong>
        </div>
        <div className="stat-card">
          <span>Linked Cases</span>
          <strong>{anomalies.filter((row) => row.case_id).length}</strong>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Detected Anomalies</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Anomaly ID</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Score</th>
                <th>Title</th>
                <th>Description</th>
                <th>Linked Case</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {anomalies.map((row, index) => {
                const anomalyId = row.id || row.anomaly_id || row.source_anomaly_id || index
                const caseId = row.case_id || null
                const isCase = row.status && row.created_at

                return (
                  <tr key={`${anomalyId}-${index}`}>
                    <td>{anomalyId}</td>
                    <td>{row.anomaly_type || row.type || row.code || '-'}</td>
                    <td>
                      <span className={badgeClass(row.severity || row.priority)}>
                        {row.severity || row.priority || '-'}
                      </span>
                    </td>
                    <td>{row.score ?? '-'}</td>
                    <td>{row.title || '-'}</td>
                    <td>{row.description || row.message || '-'}</td>
                    <td>
                      {caseId || isCase ? (
                        <Link to={`/anomaly-cases/${caseId || row.id}`} className="btn btn-secondary">
                          Open #{caseId || row.id}
                        </Link>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td>
                      {caseId || isCase ? (
                        'Linked'
                      ) : (
                        <button
                          type="button"
                          className="btn btn-primary"
                          disabled={creatingId === anomalyId}
                          onClick={() => createCaseFromAnomaly(row)}
                        >
                          {creatingId === anomalyId ? 'Creating...' : 'Create Linked Case'}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}

              {anomalies.length === 0 ? (
                <tr>
                  <td colSpan="8">No anomalies found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <p className="muted-text" style={{ marginTop: '12px' }}>
          This page refreshes automatically every 5 seconds.
        </p>
      </div>
    </div>
  )
}