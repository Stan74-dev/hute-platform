import { useEffect, useState } from 'react'
import API from '../api/client'

function money(value) {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0.00'
  return num.toFixed(2)
}

function safeText(value) {
  return value === null || value === undefined || value === '' ? '-' : String(value)
}

function parseRows(payload) {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.results)) return payload.results
  if (Array.isArray(payload?.rows)) return payload.rows
  if (Array.isArray(payload?.history)) return payload.history
  if (Array.isArray(payload?.shifts)) return payload.shifts
  return []
}

export default function AllShiftsPage() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadShifts = async () => {
    try {
      setLoading(true)
      setError('')

      const response = await API.get('/accounts/shifts/all/')
      const parsedRows = parseRows(response.data)

      setRows(parsedRows)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.error ||
          'Could not load shifts.'
      )
      setRows([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadShifts()
  }, [])

  return (
    <div>
      <div className="section-header">
        <h2>All Shifts</h2>
        <p className="muted-text">
          Review opened and closed shifts across the system.
        </p>
      </div>

      <div className="content-card" style={{ marginTop: '18px' }}>
        <button type="button" className="btn btn-secondary" onClick={loadShifts}>
          Reload
        </button>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading shifts...</p> : null}

      {error ? (
        <p className="error-text" style={{ marginTop: '16px' }}>
          {error}
        </p>
      ) : null}

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Shift Register</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Cashier</th>
                <th>Terminal</th>
                <th>Status</th>
                <th>Opening Float</th>
                <th>Expected Cash</th>
                <th>Actual Cash</th>
                <th>Variance</th>
                <th>Opened</th>
                <th>Closed</th>
              </tr>
            </thead>

            <tbody>
              {rows.map((row, index) => (
                <tr key={row.id || row.shift_id || index}>
                  <td>{safeText(row.id || row.shift_id)}</td>
                  <td>{safeText(row.cashier_username || row.cashier || row.user)}</td>
                  <td>{safeText(row.terminal_name || row.terminal_id || row.terminal)}</td>
                  <td>{safeText(row.status)}</td>
                  <td>£{money(row.opening_float)}</td>
                  <td>£{money(row.expected_cash)}</td>
                  <td>£{money(row.actual_cash)}</td>
                  <td>£{money(row.variance)}</td>
                  <td>{safeText(row.opened_at || row.opened)}</td>
                  <td>{safeText(row.closed_at || row.closed)}</td>
                </tr>
              ))}

              {rows.length === 0 ? (
                <tr>
                  <td colSpan="10">No shifts found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}