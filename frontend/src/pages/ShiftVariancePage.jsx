import { useEffect, useState } from 'react'
import API from '../api/client'

function money(value) {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0.00'
  return num.toFixed(2)
}

function numberValue(value) {
  const num = Number(value || 0)
  return Number.isNaN(num) ? 0 : num
}

export default function ShiftVariancePage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState(null)
  const [actualCash, setActualCash] = useState('')

  const loadVariance = async (actualValue = actualCash) => {
    try {
      setLoading(true)
      setError('')

      const params = new URLSearchParams()
      if (actualValue !== '') {
        params.set('actual_cash', actualValue)
      }

      const url = params.toString()
        ? `/accounts/shift-variance/?${params.toString()}`
        : '/accounts/shift-variance/'

      const response = await API.get(url)
      setData(response.data)

      const summary = response.data?.summary || {}
      if (actualValue === '' && summary.actual_cash !== undefined) {
        setActualCash(String(summary.actual_cash))
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load shift variance dashboard.')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadVariance('')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const summary = data?.summary || {}
  const rows = data?.rows || data?.shifts || data?.results || []

  const openingFloat = numberValue(summary.opening_float)
  const cashSalesTotal = numberValue(summary.cash_sales_total)
  const expectedCash = numberValue(summary.expected_cash)
  const actualCashValue = numberValue(summary.actual_cash)
  const variance = numberValue(summary.variance)

  const varianceLabel =
    variance < 0 ? 'SHORT' : variance > 0 ? 'OVER' : 'BALANCED'

  const varianceColor =
    variance < 0 ? '#b91c1c' : variance > 0 ? '#047857' : '#334155'

  return (
    <div>
      <div className="section-header">
        <h2>Shift Variance</h2>
        <p className="muted-text">
          Calculate expected cash, compare actual counted cash, and identify shortfalls or overages.
        </p>
      </div>

      <div className="content-card" style={{ marginTop: '18px' }}>
        <h3>Cash Count</h3>

        <div
          style={{
            marginTop: '12px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '12px',
            alignItems: 'end',
          }}
        >
          <label>
            Actual Cash Counted
            <input
              type="number"
              step="0.01"
              value={actualCash}
              onChange={(e) => setActualCash(e.target.value)}
              placeholder="0.00"
              style={{ width: '100%', marginTop: '6px' }}
            />
          </label>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => loadVariance(actualCash)}
            disabled={loading}
          >
            {loading ? 'Calculating...' : 'Calculate Variance'}
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              setActualCash('')
              loadVariance('')
            }}
            disabled={loading}
          >
            Reload
          </button>
        </div>

        <p className="muted-text" style={{ marginTop: '12px' }}>
          Expected Cash = Opening Float + Cash Sales only. Card or transfer payments are excluded.
        </p>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading shift variance...</p> : null}

      {error ? (
        <p className="error-text" style={{ marginTop: '16px' }}>
          {error}
        </p>
      ) : null}

      <div className="stats-grid" style={{ marginTop: '18px' }}>
        <div className="stat-card">
          <span>Opening Float</span>
          <strong>£{money(openingFloat)}</strong>
        </div>

        <div className="stat-card">
          <span>Cash Sales</span>
          <strong>£{money(cashSalesTotal)}</strong>
        </div>

        <div className="stat-card">
          <span>Expected Cash</span>
          <strong>£{money(expectedCash)}</strong>
        </div>

        <div className="stat-card">
          <span>Actual Cash</span>
          <strong>£{money(actualCashValue)}</strong>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Variance Result</h3>

        <div
          style={{
            marginTop: '14px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '12px',
          }}
        >
          <div>
            <div className="muted-text">Variance</div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: varianceColor }}>
              £{money(variance)}
            </div>
          </div>

          <div>
            <div className="muted-text">Status</div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: varianceColor }}>
              {varianceLabel}
            </div>
          </div>
        </div>
      </div>

      <div className="stats-grid" style={{ marginTop: '18px' }}>
        <div className="stat-card">
          <span>Total Shifts</span>
          <strong>{summary.total_shifts || rows.length || 0}</strong>
        </div>

        <div className="stat-card">
          <span>Short</span>
          <strong>{summary.short_count || summary.short || 0}</strong>
        </div>

        <div className="stat-card">
          <span>Over</span>
          <strong>{summary.over_count || summary.over || 0}</strong>
        </div>

        <div className="stat-card">
          <span>Balanced</span>
          <strong>{summary.balanced_count || summary.balanced || 0}</strong>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Variance Register</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Shift ID</th>
                <th>Cashier</th>
                <th>Terminal</th>
                <th>Expected</th>
                <th>Actual</th>
                <th>Variance</th>
                <th>Closed</th>
              </tr>
            </thead>

            <tbody>
              {rows.map((row, index) => (
                <tr key={row.id || row.shift_id || index}>
                  <td>{row.id || row.shift_id || '-'}</td>
                  <td>{row.cashier_username || row.user_username || row.user || row.cashier || '-'}</td>
                  <td>{row.terminal_id || row.terminal || row.terminal_name || '-'}</td>
                  <td>£{money(row.expected_cash)}</td>
                  <td>£{money(row.actual_cash)}</td>
                  <td>£{money(row.variance)}</td>
                  <td>{row.closed_at || row.closed || '-'}</td>
                </tr>
              ))}

              {rows.length === 0 ? (
                <tr>
                  <td colSpan="7">No closed shift variance rows found yet.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}