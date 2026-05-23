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

export default function TerminalsPage() {
  const [terminals, setTerminals] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')

  const loadTerminals = async () => {
    try {
      setLoading(true)
      setError('')

      const response = await API.get('/accounts/terminals/')
      setTerminals(Array.isArray(response.data) ? response.data : [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load terminals.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTerminals()

    const interval = setInterval(() => {
      loadTerminals()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const filtered = terminals.filter((terminal) => {
    const haystack = [
      terminal.terminal_name,
      terminal.terminal_id,
      terminal.cashier,
      terminal.current_cashier,
      terminal.status,
    ]
      .join(' ')
      .toLowerCase()

    return haystack.includes(search.toLowerCase())
  })

  return (
    <div>
      <div className="section-header">
        <h2>Terminal Management</h2>
        <p className="muted-text">
          View registered POS terminals, active shifts, cashier activity, and live sales.
        </p>
      </div>

      <div className="content-card" style={{ marginTop: '18px' }}>
        <h3>Search Terminals</h3>

        <div style={{ display: 'flex', gap: '10px', marginTop: '12px', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Search by terminal name, ID, cashier"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          <button type="button" className="btn btn-secondary" onClick={loadTerminals}>
            Reload
          </button>

          <button type="button" className="btn btn-secondary" onClick={() => setSearch('')}>
            Reset
          </button>
        </div>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading terminals...</p> : null}

      {error ? (
        <p className="error-text" style={{ marginTop: '16px' }}>
          {error}
        </p>
      ) : null}

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Registered Terminals</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Terminal Name</th>
                <th>Terminal ID</th>
                <th>Status</th>
                <th>Cashier</th>
                <th>Active Shift</th>
                <th>Transactions</th>
                <th>Total Sales</th>
                <th>Last Sale</th>
              </tr>
            </thead>

            <tbody>
              {filtered.map((terminal, index) => (
                <tr key={terminal.id || terminal.terminal_id || index}>
                  <td>{terminal.terminal_name || '-'}</td>
                  <td>{terminal.terminal_id || '-'}</td>

                  <td>
                    <span
                      style={{
                        color: terminal.status === 'open' ? 'green' : '#666',
                        fontWeight: 'bold',
                      }}
                    >
                      {terminal.status || 'idle'}
                    </span>
                  </td>

                  <td>{terminal.cashier || terminal.current_cashier || '-'}</td>
                  <td>{terminal.active_shift_id || '-'}</td>
                  <td>{terminal.transactions || 0}</td>
                  <td>£{money(terminal.total_sales)}</td>
                  <td>{formatDate(terminal.last_sale_at)}</td>
                </tr>
              ))}

              {filtered.length === 0 ? (
                <tr>
                  <td colSpan="8">No terminals found.</td>
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