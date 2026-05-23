import { useEffect, useMemo, useState } from 'react'
import API from '../api/client'

function formatMoney(value) {
  return Number(value || 0).toFixed(2)
}

function formatDate(value) {
  if (!value) return '-'
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

function todayString() {
  return new Date().toISOString().slice(0, 10)
}

function safeArray(value) {
  return Array.isArray(value) ? value : []
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

export default function DailySummaryPage() {
  const [selectedDate, setSelectedDate] = useState(todayString())
  const [data, setData] = useState(null)
  const [anomalyData, setAnomalyData] = useState(null)
  const [casesData, setCasesData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadSummary = async (dateValue = selectedDate) => {
    try {
      setLoading(true)
      setError('')

      const [dailyRes, anomalyRes, casesRes] = await Promise.all([
        API.get(`/accounts/daily-summary/?date=${dateValue}`),
        API.get(`/accounts/anomaly-dashboard/?date=${dateValue}`),
        API.get('/accounts/anomaly-cases/?page=1&page_size=100'),
      ])

      setData(dailyRes.data || {})
      setAnomalyData(anomalyRes.data || {})
      setCasesData(casesRes.data || {})
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load daily summary.')
      setData(null)
      setAnomalyData(null)
      setCasesData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSummary(selectedDate)

    const interval = setInterval(() => {
      loadSummary(selectedDate)
    }, 5000)

    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate])

  const summary = data?.summary || {}
  const topProducts = safeArray(data?.top_products)
  const recentSales = safeArray(data?.recent_sales || data?.sales)
  const varianceRows = safeArray(data?.variance_rows || data?.shift_variances)
  const paymentBreakdown = safeArray(data?.payment_breakdown || data?.transaction_breakdown)

  const liveAnomalies = safeArray(anomalyData?.anomalies || anomalyData?.results)
    .filter((row) => !isStoredCaseRow(row))
    .filter((row) => rowMatchesDate(row, selectedDate) || !row.detected_date)

  const allCases = safeArray(casesData?.cases || casesData?.results || casesData)
  const dayCases = allCases.filter((row) => rowMatchesDate(row, selectedDate))
  const openCases = allCases.filter((row) => String(row.status || '').toLowerCase() === 'open')
  const anomalySummary = anomalyData?.summary || {}

  const topProduct = topProducts[0] || null

  const worstShift = useMemo(() => {
    if (varianceRows.length === 0) return null

    return [...varianceRows].sort((a, b) => {
      const av = Math.abs(Number(a.variance || 0))
      const bv = Math.abs(Number(b.variance || 0))
      return bv - av
    })[0]
  }, [varianceRows])

  const transactionTotal =
    summary.transactions ||
    summary.transaction_count ||
    summary.sales_count ||
    0

  return (
    <div>
      <div className="section-header">
        <h2>Daily Summary</h2>
        <p className="muted-text">
          Daily business snapshot for revenue, profit, shifts, variance, top products, transactions, anomalies, and cases.
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

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => loadSummary(selectedDate)}
          >
            Load Summary
          </button>
        </div>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading daily summary...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}

      <div className="stats-grid" style={{ marginTop: '18px' }}>
        <div className="stat-card">
          <span>Gross Sales</span>
          <strong>£{formatMoney(summary.gross_sales || summary.total_sales || summary.total_amount)}</strong>
        </div>

        <div className="stat-card">
          <span>Refunds</span>
          <strong>£{formatMoney(summary.refund_total)}</strong>
        </div>

        <div className="stat-card">
          <span>Net Sales</span>
          <strong>£{formatMoney(summary.net_sales || summary.total_sales_net || summary.total_sales || summary.total_amount)}</strong>
        </div>

        <div className="stat-card">
          <span>Net VAT</span>
          <strong>£{formatMoney(summary.net_tax || summary.tax_amount_net || summary.tax_amount)}</strong>
        </div>

        <div className="stat-card">
          <span>Net Profit</span>
          <strong>£{formatMoney(summary.net_profit || summary.total_profit_net || summary.total_profit)}</strong>
        </div>

        <div className="stat-card">
          <span>Transactions</span>
          <strong>{transactionTotal}</strong>
        </div>
      </div>

      <div className="stats-grid" style={{ marginTop: '18px' }}>
        <div className="stat-card">
          <span>Closed Shifts</span>
          <strong>{summary.closed_shifts || 0}</strong>
        </div>

        <div className="stat-card">
          <span>Open Shifts</span>
          <strong>{summary.open_shifts || 0}</strong>
        </div>

        <div className="stat-card">
          <span>Short Variances</span>
          <strong>{summary.short_count || 0}</strong>
        </div>

        <div className="stat-card">
          <span>Over Variances</span>
          <strong>{summary.over_count || 0}</strong>
        </div>

        <div className="stat-card">
          <span>Balanced</span>
          <strong>{summary.balanced_count || 0}</strong>
        </div>
      </div>

      <div className="stats-grid" style={{ marginTop: '18px' }}>
        <div className="stat-card">
          <span>Live Anomalies</span>
          <strong>{liveAnomalies.length || anomalySummary.total_anomalies || 0}</strong>
        </div>

        <div className="stat-card">
          <span>Critical Anomalies</span>
          <strong>{anomalySummary.critical_anomalies || anomalySummary.critical || 0}</strong>
        </div>

        <div className="stat-card">
          <span>High Anomalies</span>
          <strong>{anomalySummary.high_anomalies || anomalySummary.high || 0}</strong>
        </div>

        <div className="stat-card">
          <span>Linked Cases Today</span>
          <strong>{dayCases.length}</strong>
        </div>

        <div className="stat-card">
          <span>Open Cases</span>
          <strong>{openCases.length}</strong>
        </div>
      </div>

      <div className="card-grid" style={{ marginTop: '20px' }}>
        <div className="content-card">
          <h3>Top Product</h3>

          {!topProduct ? (
            <p style={{ marginTop: '12px' }}>No product data for this day.</p>
          ) : (
            <div style={{ marginTop: '12px' }}>
              <p><strong>Name:</strong> {topProduct.product_name || topProduct.product || '-'}</p>
              <p><strong>SKU:</strong> {topProduct.product_sku || topProduct.sku || '-'}</p>
              <p><strong>Qty Sold:</strong> {topProduct.qty_sold || topProduct.quantity || 0}</p>
              <p><strong>Revenue:</strong> £{formatMoney(topProduct.revenue || topProduct.total_revenue)}</p>
            </div>
          )}
        </div>

        <div className="content-card">
          <h3>Worst Shift Variance</h3>

          {!worstShift ? (
            <p style={{ marginTop: '12px' }}>No shift variance recorded for this day.</p>
          ) : (
            <div style={{ marginTop: '12px' }}>
              <p><strong>Shift ID:</strong> {worstShift.shift_id || '-'}</p>
              <p><strong>Cashier:</strong> {worstShift.cashier || worstShift.cashier_username || '-'}</p>
              <p><strong>Terminal:</strong> {worstShift.terminal || worstShift.terminal_id || '-'}</p>
              <p><strong>Status:</strong> {worstShift.status || '-'}</p>
              <p><strong>Expected Cash:</strong> £{formatMoney(worstShift.expected_cash)}</p>
              <p><strong>Actual Cash:</strong> £{formatMoney(worstShift.actual_cash)}</p>
              <p><strong>Variance:</strong> £{formatMoney(worstShift.variance)}</p>
              <p><strong>Closed At:</strong> {formatDate(worstShift.closed_at)}</p>
            </div>
          )}
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Anomalies for Selected Day</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Anomaly ID</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Title</th>
                <th>Linked Case</th>
              </tr>
            </thead>

            <tbody>
              {liveAnomalies.map((row, index) => (
                <tr key={row.id || row.anomaly_id || index}>
                  <td>{row.id || row.anomaly_id || '-'}</td>
                  <td>{row.type || row.anomaly_type || row.code || '-'}</td>
                  <td>{row.severity || row.priority || '-'}</td>
                  <td>{row.title || row.message || '-'}</td>
                  <td>{row.case_id || '-'}</td>
                </tr>
              ))}

              {liveAnomalies.length === 0 ? (
                <tr>
                  <td colSpan="5">No anomalies found for this day.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Cases for Selected Day</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Title</th>
                <th>Created</th>
              </tr>
            </thead>

            <tbody>
              {dayCases.map((row, index) => (
                <tr key={row.id || index}>
                  <td>{row.id || '-'}</td>
                  <td>{row.priority || '-'}</td>
                  <td>{row.status || '-'}</td>
                  <td>{row.title || '-'}</td>
                  <td>{formatDate(row.created_at)}</td>
                </tr>
              ))}

              {dayCases.length === 0 ? (
                <tr>
                  <td colSpan="5">No cases found for this day.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Payment / Transaction Breakdown</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Payment Method</th>
                <th>Transactions</th>
                <th>Total Sales</th>
                <th>Sales Tax / VAT</th>
              </tr>
            </thead>

            <tbody>
              {paymentBreakdown.map((row, index) => (
                <tr key={row.payment_method || index}>
                  <td>{row.payment_method || '-'}</td>
                  <td>{row.transactions || row.sales_count || 0}</td>
                  <td>£{formatMoney(row.total_amount || row.sales)}</td>
                  <td>£{formatMoney(row.tax_amount || row.tax)}</td>
                </tr>
              ))}

              {paymentBreakdown.length === 0 ? (
                <tr>
                  <td colSpan="4">No transaction breakdown found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Top Products</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>SKU</th>
                <th>Qty Sold</th>
                <th>Revenue</th>
                <th>Sales Tax / VAT</th>
              </tr>
            </thead>

            <tbody>
              {topProducts.map((row, index) => (
                <tr key={row.product_id || index}>
                  <td>{row.product_name || row.product || '-'}</td>
                  <td>{row.product_sku || row.sku || '-'}</td>
                  <td>{row.qty_sold || row.quantity || 0}</td>
                  <td>£{formatMoney(row.revenue || row.total_revenue)}</td>
                  <td>£{formatMoney(row.tax_amount || row.tax)}</td>
                </tr>
              ))}

              {topProducts.length === 0 ? (
                <tr>
                  <td colSpan="5">No top products found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Recent Sales</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Receipt</th>
                <th>Cashier</th>
                <th>Warehouse</th>
                <th>Shift</th>
                <th>Payment</th>
                <th>Sales</th>
                <th>Sales Tax / VAT</th>
                <th>Profit</th>
              </tr>
            </thead>

            <tbody>
              {recentSales.map((row) => (
                <tr key={row.id || row.sale_id || row.receipt_number}>
                  <td>{formatDate(row.created_at)}</td>
                  <td>{row.receipt_number || row.receipt || '-'}</td>
                  <td>{row.cashier_username || row.cashier || '-'}</td>
                  <td>{row.warehouse_name || row.warehouse || '-'}</td>
                  <td>{row.shift_id || row.shift || '-'}</td>
                  <td>{row.payment_method || row.payment || '-'}</td>
                  <td>£{formatMoney(row.total_amount || row.total)}</td>
                  <td>£{formatMoney(row.tax_amount || row.tax)}</td>
                  <td>£{formatMoney(row.total_profit || row.profit)}</td>
                </tr>
              ))}

              {recentSales.length === 0 ? (
                <tr>
                  <td colSpan="9">No sales for this day.</td>
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
