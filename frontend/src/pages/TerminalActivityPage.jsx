import { useEffect, useState } from 'react'
import API from '../api/client'

function money(value) {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0.00'
  return num.toFixed(2)
}

function formatDate(value) {
  if (!value) return '-'

  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

function parseRows(payload) {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.rows)) return payload.rows
  if (Array.isArray(payload?.results)) return payload.results
  if (Array.isArray(payload?.terminals)) return payload.terminals
  return []
}

export default function TerminalActivityPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState(null)
  const [search, setSearch] = useState('')

  const loadActivity = async () => {
    try {
      setLoading(true)
      setError('')

      const response = await API.get('/accounts/terminal-activity/')
      setData(response.data || {})
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load terminal activity.')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadActivity()

    const interval = setInterval(() => {
      loadActivity()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const rows = parseRows(data)

  const filteredRows = rows.filter((row) => {
    const haystack = [
      row.terminal_id,
      row.terminal_name,
      row.terminal,
      row.cashier,
      row.current_user,
      row.current_user_username,
    ]
      .join(' ')
      .toLowerCase()

    return haystack.includes(search.toLowerCase())
  })

  const activeCount = filteredRows.filter((row) =>
    ['open', 'active', 'online'].includes(String(row.status || '').toLowerCase())
  ).length

  const inactiveCount = Math.max(filteredRows.length - activeCount, 0)

  return (
    <div>
      <div className="section-header">
        <h2>Terminal Activity</h2>
        <p className="muted-text">
          Review terminal status, live transactions, cashier activity, and recent usage.
        </p>
      </div>

      <div className="content-card" style={{ marginTop: '18px' }}>
        <h3>Filters</h3>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '12px' }}>
          <input
            type="text"
            placeholder="Search terminal, cashier, ID"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          <button type="button" className="btn btn-secondary" onClick={loadActivity}>
            Reload
          </button>

          <button type="button" className="btn btn-secondary" onClick={() => setSearch('')}>
            Reset
          </button>
        </div>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading terminal activity...</p> : null}

      {error ? (
        <p className="error-text" style={{ marginTop: '16px' }}>
          {error}
        </p>
      ) : null}

      <div className="stats-grid" style={{ marginTop: '18px' }}>
        <div className="stat-card">
          <span>Total Terminals</span>
          <strong>{filteredRows.length}</strong>
        </div>

        <div className="stat-card">
          <span>Active</span>
          <strong>{activeCount}</strong>
        </div>

        <div className="stat-card">
          <span>Inactive</span>
          <strong>{inactiveCount}</strong>
        </div>

        <div className="stat-card">
          <span>Total Transactions</span>
          <strong>
            {filteredRows.reduce((sum, row) => sum + Number(row.transactions || row.sales_count || 0), 0)}
          </strong>
        </div>

        <div className="stat-card">
          <span>Total Sales</span>
          <strong>
            £
            {money(
              filteredRows.reduce(
                (sum, row) => sum + Number(row.total_sales || row.total_amount || 0),
                0
              )
            )}
          </strong>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Terminal Activity Register</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Terminal ID</th>
                <th>Name</th>
                <th>Status</th>
                <th>Cashier</th>
                <th>Transactions</th>
                <th>Total Sales</th>
                <th>Last Sale</th>
                <th>Active Shift</th>
              </tr>
            </thead>

            <tbody>
              {filteredRows.map((row, index) => (
                <tr key={row.id || row.terminal_id || index}>
                  <td>{row.terminal_id || row.id || '-'}</td>
                  <td>{row.terminal_name || row.terminal || row.name || '-'}</td>

                  <td>
                    <span
                      style={{
                        color:
                          ['open', 'active', 'online'].includes(
                            String(row.status || '').toLowerCase()
                          )
                            ? 'green'
                            : '#666',
                        fontWeight: 'bold',
                      }}
                    >
                      {row.status || 'idle'}
                    </span>
                  </td>

                  <td>
                    {row.cashier ||
                      row.current_cashier ||
                      row.current_user_username ||
                      row.user_username ||
                      '-'}
                  </td>

                  <td>{row.transactions || row.sales_count || 0}</td>

                  <td>£{money(row.total_sales || row.total_amount)}</td>

                  <td>{formatDate(row.last_sale_at || row.last_active_at || row.last_seen)}</td>

                  <td>{row.active_shift_id || row.shift_id || '-'}</td>
                </tr>
              ))}

              {filteredRows.length === 0 ? (
                <tr>
                  <td colSpan="8">No terminal activity found.</td>
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