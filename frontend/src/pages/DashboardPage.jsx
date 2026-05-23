import { useEffect, useState } from 'react'
import API from '../api/client'

function money(value) {
  return new Intl.NumberFormat('en-GB', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value || 0))
}

function safeArray(value) {
  return Array.isArray(value) ? value : []
}

function liveAnomalies(payload) {
  const rows = safeArray(payload?.anomalies || payload?.results)
  return rows.filter((row) => !(row.created_at && (row.source_anomaly_id || row.linked_anomaly_id)))
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState(null)

  const loadDashboard = async () => {
    try {
      setLoading(true)
      setError('')

      const [dashboardRes, anomalyRes, varianceRes, casesRes] = await Promise.all([
        API.get('/dashboard/'),
        API.get('/accounts/anomaly-dashboard/'),
        API.get('/accounts/shift-variance/'),
        API.get('/accounts/anomaly-cases/?page=1&page_size=100'),
      ])

      const dashboard = dashboardRes.data || {}
      const anomaly = anomalyRes.data || {}
      const variance = varianceRes.data || {}
      const allCases = safeArray(casesRes.data?.cases || casesRes.data?.results || casesRes.data)
      const openCases = allCases.filter((row) => String(row.status || '').toLowerCase() === 'open')
      const anomalies = liveAnomalies(anomaly)

      setData({
        kpis: {
          total_sales: dashboard.summary?.total_sales || dashboard.summary?.total_amount || 0,
          total_profit: dashboard.summary?.total_profit || 0,
          total_transactions: dashboard.summary?.transactions || dashboard.summary?.sales_count || 0,
          total_shifts: variance.summary?.total_shifts || 0,
          open_cases: openCases.length,
          breached_cases: allCases.filter((row) => row.sla_breached).length,
          escalated_cases: allCases.filter((row) => Number(row.escalation_level || 0) > 0).length,
          anomalies_today: anomalies.length,
        },
        anomaly_summary: {
          ...(anomaly.summary || {}),
          total: anomalies.length,
          total_anomalies: anomalies.length,
          open_cases: openCases.length,
        },
        shift_variance_summary: variance.summary || {},
        recent_priority_anomalies: anomalies,
        top_open_cases: openCases,
      })
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.error || err.message || 'Could not load dashboard.')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboard()
    const interval = setInterval(loadDashboard, 5000)
    return () => clearInterval(interval)
  }, [])

  const kpis = data?.kpis || {}
  const anomalySummary = data?.anomaly_summary || {}
  const shiftVarianceSummary = data?.shift_variance_summary || {}
  const recentPriorityAnomalies = data?.recent_priority_anomalies || []
  const topOpenCases = data?.top_open_cases || []

  return (
    <div>
      <div className="section-header">
        <h2>Dashboard</h2>
        <p className="muted-text">Operational overview of sales, cases, anomalies, and shift health.</p>
      </div>

      <div className="content-card" style={{ marginTop: '18px' }}>
        <button type="button" className="btn btn-secondary" onClick={loadDashboard}>Reload</button>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading dashboard...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}

      {!loading && !error ? (
        <>
          <div className="stats-grid" style={{ marginTop: '18px' }}>
            <div className="stat-card"><span>Total Sales</span><strong>£{money(kpis.total_sales)}</strong></div>
            <div className="stat-card"><span>Total Profit</span><strong>£{money(kpis.total_profit)}</strong></div>
            <div className="stat-card"><span>Transactions</span><strong>{kpis.total_transactions || 0}</strong></div>
            <div className="stat-card"><span>Shifts</span><strong>{kpis.total_shifts || 0}</strong></div>
            <div className="stat-card"><span>Open Cases</span><strong>{kpis.open_cases || 0}</strong></div>
            <div className="stat-card"><span>Live Anomalies</span><strong>{kpis.anomalies_today || 0}</strong></div>
            <div className="stat-card"><span>Breached Cases</span><strong>{kpis.breached_cases || 0}</strong></div>
            <div className="stat-card"><span>Escalated Cases</span><strong>{kpis.escalated_cases || 0}</strong></div>
          </div>

          <div className="card-grid" style={{ marginTop: '20px' }}>
            <div className="content-card">
              <h3>Anomaly Summary</h3>
              <p><strong>Critical:</strong> {anomalySummary.critical || 0}</p>
              <p><strong>High:</strong> {anomalySummary.high || 0}</p>
              <p><strong>Medium:</strong> {anomalySummary.medium || 0}</p>
              <p><strong>Low:</strong> {anomalySummary.low || 0}</p>
            </div>
            <div className="content-card">
              <h3>Shift Variance Summary</h3>
              <p><strong>Short:</strong> {shiftVarianceSummary.short_count || shiftVarianceSummary.short || 0}</p>
              <p><strong>Over:</strong> {shiftVarianceSummary.over_count || shiftVarianceSummary.over || 0}</p>
              <p><strong>Balanced:</strong> {shiftVarianceSummary.balanced_count || shiftVarianceSummary.balanced || 0}</p>
            </div>
          </div>

          <div className="card-grid" style={{ marginTop: '20px' }}>
            <div className="content-card">
              <h3>Recent Priority Anomalies</h3>
              <div className="table-wrap" style={{ marginTop: '12px' }}>
                <table>
                  <thead><tr><th>Priority</th><th>Status</th><th>Title</th></tr></thead>
                  <tbody>
                    {recentPriorityAnomalies.map((row, index) => (
                      <tr key={row.id || index}><td>{row.priority || row.severity || '-'}</td><td>{row.status || '-'}</td><td>{row.title || '-'}</td></tr>
                    ))}
                    {recentPriorityAnomalies.length === 0 ? <tr><td colSpan="3">No anomalies found.</td></tr> : null}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="content-card">
              <h3>Open Cases</h3>
              <div className="table-wrap" style={{ marginTop: '12px' }}>
                <table>
                  <thead><tr><th>ID</th><th>Priority</th><th>Status</th><th>Title</th></tr></thead>
                  <tbody>
                    {topOpenCases.map((row, index) => (
                      <tr key={row.id || index}><td>{row.id || '-'}</td><td>{row.priority || '-'}</td><td>{row.status || '-'}</td><td>{row.title || '-'}</td></tr>
                    ))}
                    {topOpenCases.length === 0 ? <tr><td colSpan="4">No open cases found.</td></tr> : null}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}
