import { useEffect, useState } from 'react'
import API from '../api/client'

function money(value) {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0.00'
  return num.toFixed(2)
}

function safeArray(value) {
  return Array.isArray(value) ? value : []
}

function todayString() {
  return new Date().toISOString().slice(0, 10)
}

function liveAnomalies(payload) {
  const rows = safeArray(payload?.anomalies || payload?.results)
  return rows.filter((row) => !(row.created_at && (row.source_anomaly_id || row.linked_anomaly_id)))
}

export default function ExecutiveDashboardPage() {
  const [selectedDate, setSelectedDate] = useState(todayString())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [data, setData] = useState({ summary: {}, anomaly_summary: {}, shift_variance_summary: {}, recent_priority_anomalies: [], recent_sales: [], open_cases: [] })

  const loadData = async (dateValue = selectedDate) => {
    try {
      setLoading(true)
      setError('')

      const [dashboardRes, anomalyRes, varianceRes, casesRes] = await Promise.all([
        API.get(`/dashboard/?date=${dateValue}`),
        API.get(`/accounts/anomaly-dashboard/?date=${dateValue}`),
        API.get(`/accounts/shift-variance/?date=${dateValue}`),
        API.get('/accounts/anomaly-cases/?page=1&page_size=100'),
      ])

      const dashboard = dashboardRes.data || {}
      const anomaly = anomalyRes.data || {}
      const variance = varianceRes.data || {}
      const allCases = safeArray(casesRes.data?.cases || casesRes.data?.results || casesRes.data)
      const openCases = allCases.filter((row) => String(row.status || '').toLowerCase() === 'open')
      const anomalies = liveAnomalies(anomaly)
      const anomalySummary = anomaly.summary || {}
      const varianceSummary = variance.summary || {}

      setData({
        summary: {
          ...(dashboard.summary || {}),
          open_cases: openCases.length,
          breached_cases: allCases.filter((row) => row.sla_breached).length,
          escalated_cases: allCases.filter((row) => Number(row.escalation_level || 0) > 0).length,
          anomalies_today: anomalies.length,
        },
        anomaly_summary: { ...anomalySummary, total: anomalies.length, total_anomalies: anomalies.length, open_cases: openCases.length },
        shift_variance_summary: {
          short: varianceSummary.short || varianceSummary.short_count || 0,
          over: varianceSummary.over || varianceSummary.over_count || 0,
          balanced: varianceSummary.balanced || varianceSummary.balanced_count || 0,
        },
        recent_priority_anomalies: anomalies.slice(0, 20),
        recent_sales: safeArray(dashboard.recent_sales || dashboard.sales).slice(0, 20),
        open_cases: openCases.slice(0, 20),
      })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load executive dashboard.')
      setData({ summary: {}, anomaly_summary: {}, shift_variance_summary: {}, recent_priority_anomalies: [], recent_sales: [], open_cases: [] })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData(selectedDate)
    const interval = setInterval(() => loadData(selectedDate), 5000)
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate])

  return (
    <div>
      <div className="section-header">
        <h2>Executive Dashboard</h2>
        <p className="muted-text">High-level overview of business performance, anomaly risk, and shift health.</p>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Date Selection</h3>
        <div style={{ marginTop: '12px', display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} />
          <button type="button" className="btn btn-secondary" onClick={() => loadData(selectedDate)} disabled={loading}>{loading ? 'Loading...' : 'Load'}</button>
        </div>
        {error ? <p className="error-text" style={{ marginTop: '12px' }}>{error}</p> : null}
      </div>

      <div style={{ marginTop: '16px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '12px' }}>
        <div className="content-card"><div className="muted-text">Total Sales</div><h3 style={{ marginTop: '8px' }}>£{money(data.summary.total_sales || data.summary.total_amount)}</h3></div>
        <div className="content-card"><div className="muted-text">Total Profit</div><h3 style={{ marginTop: '8px' }}>£{money(data.summary.total_profit)}</h3></div>
        <div className="content-card"><div className="muted-text">Transactions</div><h3 style={{ marginTop: '8px' }}>{data.summary.transactions || data.summary.sales_count || 0}</h3></div>
        <div className="content-card"><div className="muted-text">Open Cases</div><h3 style={{ marginTop: '8px' }}>{data.summary.open_cases || 0}</h3></div>
        <div className="content-card"><div className="muted-text">Breached Cases</div><h3 style={{ marginTop: '8px' }}>{data.summary.breached_cases || 0}</h3></div>
        <div className="content-card"><div className="muted-text">Escalated Cases</div><h3 style={{ marginTop: '8px' }}>{data.summary.escalated_cases || 0}</h3></div>
        <div className="content-card"><div className="muted-text">Live Anomalies</div><h3 style={{ marginTop: '8px' }}>{data.summary.anomalies_today || 0}</h3></div>
      </div>

      <div style={{ marginTop: '18px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '14px' }}>
        <div className="content-card"><h3>Anomaly Summary</h3><div style={{ marginTop: '14px', lineHeight: 2 }}><div><strong>Critical:</strong> {data.anomaly_summary.critical || 0}</div><div><strong>High:</strong> {data.anomaly_summary.high || 0}</div><div><strong>Medium:</strong> {data.anomaly_summary.medium || 0}</div><div><strong>Low:</strong> {data.anomaly_summary.low || 0}</div></div></div>
        <div className="content-card"><h3>Shift Variance Summary</h3><div style={{ marginTop: '14px', lineHeight: 2 }}><div><strong>Short:</strong> {data.shift_variance_summary.short || 0}</div><div><strong>Over:</strong> {data.shift_variance_summary.over || 0}</div><div><strong>Balanced:</strong> {data.shift_variance_summary.balanced || 0}</div></div></div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}><h3>Recent Priority Anomalies</h3><div className="table-wrap" style={{ marginTop: '12px' }}><table><thead><tr><th>Priority</th><th>Status</th><th>Title</th><th>Detected</th></tr></thead><tbody>{data.recent_priority_anomalies.map((row, index) => (<tr key={row.id || index}><td>{row.priority || row.severity || '-'}</td><td>{row.status || '-'}</td><td>{row.title || '-'}</td><td>{row.detected_date || row.created_at || '-'}</td></tr>))}{data.recent_priority_anomalies.length === 0 ? <tr><td colSpan="4">No priority anomalies found.</td></tr> : null}</tbody></table></div></div>

      <div className="content-card" style={{ marginTop: '20px' }}><h3>Open Cases</h3><div className="table-wrap" style={{ marginTop: '12px' }}><table><thead><tr><th>ID</th><th>Priority</th><th>Status</th><th>Title</th><th>Created</th></tr></thead><tbody>{data.open_cases.map((row, index) => (<tr key={row.id || index}><td>{row.id || '-'}</td><td>{row.priority || '-'}</td><td>{row.status || '-'}</td><td>{row.title || '-'}</td><td>{row.created_at || '-'}</td></tr>))}{data.open_cases.length === 0 ? <tr><td colSpan="5">No open cases found.</td></tr> : null}</tbody></table></div></div>

      <div className="content-card" style={{ marginTop: '20px' }}><h3>Recent Sales</h3><div className="table-wrap" style={{ marginTop: '12px' }}><table><thead><tr><th>Receipt</th><th>Cashier</th><th>Warehouse</th><th>Payment</th><th>Total</th><th>Created</th></tr></thead><tbody>{data.recent_sales.map((row, index) => (<tr key={row.id || row.receipt_number || index}><td>{row.receipt_number || '-'}</td><td>{row.cashier_username || '-'}</td><td>{row.warehouse_name || '-'}</td><td>{row.payment_method || '-'}</td><td>£{money(row.total_amount)}</td><td>{row.created_at || '-'}</td></tr>))}{data.recent_sales.length === 0 ? <tr><td colSpan="6">No recent sales found.</td></tr> : null}</tbody></table></div></div>
    </div>
  )
}
