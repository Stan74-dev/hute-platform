import { useEffect, useMemo, useState } from 'react'
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

function rowMatchesDate(row, dateValue) {
  const values = [
    row.date,
    row.detected_date,
    row.created_at,
    row.updated_at,
    row.closed_at,
    row.opened_at,
    row.opened,
    row.closed,
  ]

  return values.some((value) => String(value || '').slice(0, 10) === dateValue)
}

function isStoredCaseRow(row) {
  return Boolean(
    row?.created_at &&
      (row?.source_anomaly_id || row?.linked_anomaly_id || row?.metadata?.source_anomaly_id)
  )
}

export default function DayDetailPage() {
  const [selectedDate, setSelectedDate] = useState(todayString())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [data, setData] = useState({
    summary: {},
    sales: [],
    anomalies: [],
    cases: [],
    shifts: [],
    products: [],
    hourly_breakdown: [],
  })

  const loadData = async (dateValue = selectedDate) => {
    try {
      setLoading(true)
      setError('')

      const [dailyRes, anomalyRes, casesRes, shiftsRes] = await Promise.all([
        API.get(`/accounts/daily-summary/?date=${dateValue}`),
        API.get(`/accounts/anomaly-dashboard/?date=${dateValue}`),
        API.get('/accounts/anomaly-cases/'),
        API.get('/accounts/shifts/all/'),
      ])

      const daily = dailyRes.data || {}
      const anomaly = anomalyRes.data || {}
      const casesPayload = casesRes.data || {}
      const shiftsPayload = shiftsRes.data || {}

      const allCases = safeArray(casesPayload.cases || casesPayload.results || casesPayload)
      const allShifts = safeArray(shiftsPayload.rows || shiftsPayload.results || shiftsPayload.history || shiftsPayload)

      const dayCases = allCases.filter((row) => rowMatchesDate(row, dateValue))
      const dayShifts = allShifts.filter((row) => rowMatchesDate(row, dateValue))

      setData({
        summary: daily.summary || {},
        sales: safeArray(daily.sales || daily.recent_sales || daily.results),
        anomalies: safeArray(anomaly.anomalies || anomaly.results).filter((row) => !isStoredCaseRow(row)),
        cases: dayCases,
        shifts: dayShifts.length ? dayShifts : safeArray(daily.shifts || daily.closed_shifts || daily.open_shifts),
        products: safeArray(daily.top_products || daily.products),
        hourly_breakdown: safeArray(daily.hourly_breakdown),
      })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load day detail.')
      setData({
        summary: {},
        sales: [],
        anomalies: [],
        cases: [],
        shifts: [],
        products: [],
        hourly_breakdown: [],
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData(selectedDate)

    const interval = setInterval(() => {
      loadData(selectedDate)
    }, 5000)

    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate])

  const salesRows = useMemo(() => data.sales, [data.sales])

  const handleExportPdf = async () => {
    try {
      const { data: pdfPayload } = await API.get(`/accounts/shift/report-pdf/?date=${selectedDate}`)
      console.log('PDF payload:', pdfPayload)
      alert('PDF export payload prepared successfully.')
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to prepare PDF export.')
    }
  }

  return (
    <div>
      <div className="section-header">
        <h2>Day Investigation</h2>
        <p className="muted-text">
          Drill into sales, anomalies, cases, and shift variances for a single day.
        </p>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Date Selection</h3>

        <div style={{ marginTop: '12px', display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />

          <button onClick={() => loadData(selectedDate)} disabled={loading}>
            {loading ? 'Loading...' : 'Load'}
          </button>

          <button onClick={handleExportPdf} className="primary">
            Export PDF
          </button>
        </div>

        {error ? <p className="error-text" style={{ marginTop: '12px' }}>{error}</p> : null}
      </div>

      <div className="stats-grid" style={{ marginTop: '20px' }}>
        <div className="stat-card">
          <span>Sales</span>
          <strong>{data.summary.sales_count || data.summary.transactions || salesRows.length || 0}</strong>
        </div>

        <div className="stat-card">
          <span>Anomalies</span>
          <strong>{data.anomalies.length}</strong>
        </div>

        <div className="stat-card">
          <span>Cases</span>
          <strong>{data.cases.length}</strong>
        </div>

        <div className="stat-card">
          <span>Shifts</span>
          <strong>{data.shifts.length}</strong>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Sales</h3>
        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Receipt</th>
                <th>Cashier</th>
                <th>Warehouse</th>
                <th>Shift</th>
                <th>Payment</th>
                <th>Total</th>
                <th>Profit</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {salesRows.map((row, index) => (
                <tr key={row.id || row.receipt_number || index}>
                  <td>{row.receipt_number || row.receipt || '-'}</td>
                  <td>{row.cashier_username || row.cashier || '-'}</td>
                  <td>{row.warehouse_name || row.warehouse || '-'}</td>
                  <td>{row.shift_id || row.shift || '-'}</td>
                  <td>{row.payment_method || row.payment || '-'}</td>
                  <td>£{money(row.total_amount || row.total)}</td>
                  <td>£{money(row.total_profit || row.profit)}</td>
                  <td>{row.created_at || row.created || '-'}</td>
                </tr>
              ))}

              {salesRows.length === 0 ? (
                <tr><td colSpan="8">No sales found.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Anomalies</h3>
        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Type</th>
                <th>Severity</th>
                <th>Title</th>
                <th>Case</th>
              </tr>
            </thead>
            <tbody>
              {data.anomalies.map((row, index) => (
                <tr key={row.id || index}>
                  <td>{row.type || row.code || '-'}</td>
                  <td>{row.severity || row.level || row.priority || '-'}</td>
                  <td>{row.title || row.message || '-'}</td>
                  <td>{row.case_id || row.case || '-'}</td>
                </tr>
              ))}

              {data.anomalies.length === 0 ? (
                <tr><td colSpan="4">No anomalies found.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Cases</h3>
        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Assigned</th>
                <th>SLA</th>
                <th>Esc.</th>
                <th>Title</th>
              </tr>
            </thead>
            <tbody>
              {data.cases.map((row, index) => (
                <tr key={row.id || index}>
                  <td>{row.id || '-'}</td>
                  <td>{row.priority || '-'}</td>
                  <td>{row.status || '-'}</td>
                  <td>{row.assigned || '-'}</td>
                  <td>{row.sla || '-'}</td>
                  <td>{row.esc || '-'}</td>
                  <td>{row.title || '-'}</td>
                </tr>
              ))}

              {data.cases.length === 0 ? (
                <tr><td colSpan="7">No cases found.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Shifts</h3>
        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Cashier</th>
                <th>Terminal</th>
                <th>Status</th>
                <th>Expected Cash</th>
                <th>Actual Cash</th>
                <th>Variance</th>
                <th>Opened</th>
                <th>Closed</th>
              </tr>
            </thead>
            <tbody>
              {data.shifts.map((row, index) => (
                <tr key={row.id || row.shift_id || index}>
                  <td>{row.id || row.shift_id || '-'}</td>
                  <td>{row.cashier || row.cashier_username || '-'}</td>
                  <td>{row.terminal || row.terminal_name || '-'}</td>
                  <td>{row.status || '-'}</td>
                  <td>£{money(row.expected_cash)}</td>
                  <td>£{money(row.actual_cash)}</td>
                  <td>£{money(row.variance)}</td>
                  <td>{row.opened_at || row.opened || '-'}</td>
                  <td>{row.closed_at || row.closed || '-'}</td>
                </tr>
              ))}

              {data.shifts.length === 0 ? (
                <tr><td colSpan="9">No shifts found.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Product Summary</h3>
        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>SKU</th>
                <th>Qty Sold</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              {data.products.map((row, index) => (
                <tr key={row.product_id || row.sku || index}>
                  <td>{row.product_name || row.product || '-'}</td>
                  <td>{row.product_sku || row.sku || '-'}</td>
                  <td>{row.qty_sold || row.quantity || 0}</td>
                  <td>£{money(row.revenue || row.total_amount || row.total)}</td>
                </tr>
              ))}

              {data.products.length === 0 ? (
                <tr><td colSpan="4">No product summary found.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <p className="muted-text" style={{ marginTop: '12px' }}>
        This page refreshes automatically every 5 seconds.
      </p>
    </div>
  )
}