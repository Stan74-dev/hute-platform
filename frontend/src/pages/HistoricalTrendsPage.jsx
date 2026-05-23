import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import API from '../api/client'

function money(value) {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0.00'
  return num.toFixed(2)
}

function todayString() {
  return new Date().toISOString().slice(0, 10)
}

function parseRows(payload) {
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload?.rows)) return payload.rows
  if (Array.isArray(payload?.results)) return payload.results
  if (Array.isArray(payload?.recent_snapshots)) return payload.recent_snapshots
  if (Array.isArray(payload?.charts?.points)) return payload.charts.points
  return []
}

export default function HistoricalTrendsPage() {
  const navigate = useNavigate()

  const [selectedDate, setSelectedDate] = useState(todayString())
  const [days, setDays] = useState(30)
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadTrends = async () => {
    try {
      setLoading(true)
      setError('')

      const response = await API.get(`/accounts/historical-trends/?days=${days}`)
      setRows(parseRows(response.data))
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load historical trends.')
      setRows([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTrends()

    const interval = setInterval(() => {
      loadTrends()
    }, 5000)

    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days])

  const selectedRow = useMemo(() => {
    return rows.find((row) => row.date === selectedDate) || rows[rows.length - 1] || {}
  }, [rows, selectedDate])

  const chartPoints = rows.map((row) => ({
    date: row.date,
    total_sales: Number(row.total_sales || row.total_amount || 0),
    total_profit: Number(row.total_profit || 0),
    transactions: Number(row.transactions || row.sales_count || 0),
    total_quantity: Number(row.total_quantity || 0),
  }))

  const goToDay = (date) => {
    if (!date) return
    navigate(`/day-detail?date=${date}`)
  }

  return (
    <div>
      <div className="section-header">
        <h2>Historical Trends</h2>
        <p className="muted-text">
          Review sales, profit, transactions, and quantity trends from live sales data.
        </p>
      </div>

      <div className="content-card" style={{ marginTop: '18px' }}>
        <h3>Filters</h3>

        <div style={{ display: 'flex', gap: '10px', marginTop: '12px', flexWrap: 'wrap' }}>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />

          <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={60}>Last 60 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>

          <button type="button" className="btn btn-secondary" onClick={loadTrends}>
            Reload
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => goToDay(selectedDate)}
          >
            Investigate Day
          </button>
        </div>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading historical trends...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}

      <div className="stats-grid" style={{ marginTop: '18px' }}>
        <div className="stat-card">
          <span>Selected Date</span>
          <strong>{selectedRow.date || selectedDate}</strong>
        </div>
        <div className="stat-card">
          <span>Total Sales</span>
          <strong>£{money(selectedRow.total_sales || selectedRow.total_amount)}</strong>
        </div>
        <div className="stat-card">
          <span>Total Profit</span>
          <strong>£{money(selectedRow.total_profit)}</strong>
        </div>
        <div className="stat-card">
          <span>Transactions</span>
          <strong>{selectedRow.transactions || selectedRow.sales_count || 0}</strong>
        </div>
        <div className="stat-card">
          <span>Quantity Sold</span>
          <strong>{selectedRow.total_quantity || 0}</strong>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Sales Trend</h3>
        <div style={{ width: '100%', height: 300, marginTop: '12px' }}>
          <ResponsiveContainer>
            <LineChart
              data={chartPoints}
              onClick={(state) => {
                if (state?.activeLabel) goToDay(state.activeLabel)
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="total_sales" name="Sales" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Profit Trend</h3>
        <div style={{ width: '100%', height: 300, marginTop: '12px' }}>
          <ResponsiveContainer>
            <LineChart
              data={chartPoints}
              onClick={(state) => {
                if (state?.activeLabel) goToDay(state.activeLabel)
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="total_profit" name="Profit" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Transactions Trend</h3>
        <div style={{ width: '100%', height: 300, marginTop: '12px' }}>
          <ResponsiveContainer>
            <LineChart
              data={chartPoints}
              onClick={(state) => {
                if (state?.activeLabel) goToDay(state.activeLabel)
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="transactions" name="Transactions" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Daily Trend Register</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Sales</th>
                <th>Profit</th>
                <th>Transactions</th>
                <th>Quantity</th>
                <th>Tax</th>
                <th>Cost</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {rows.map((row) => (
                <tr key={row.date}>
                  <td>{row.date}</td>
                  <td>£{money(row.total_sales || row.total_amount)}</td>
                  <td>£{money(row.total_profit)}</td>
                  <td>{row.transactions || row.sales_count || 0}</td>
                  <td>{row.total_quantity || 0}</td>
                  <td>£{money(row.tax_amount)}</td>
                  <td>£{money(row.total_cost)}</td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => goToDay(row.date)}
                    >
                      Investigate
                    </button>
                  </td>
                </tr>
              ))}

              {rows.length === 0 ? (
                <tr>
                  <td colSpan="8">No historical trend data found.</td>
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