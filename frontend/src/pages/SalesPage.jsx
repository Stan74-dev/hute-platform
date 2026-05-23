import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import API from '../api/client'

function money(value) {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0.00'
  return num.toFixed(2)
}

function safeText(value) {
  return value === null || value === undefined || value === '' ? '-' : String(value)
}

function parseSalesPayload(payload) {
  if (Array.isArray(payload)) {
    return payload
  }

  if (Array.isArray(payload?.sales)) {
    return payload.sales
  }

  if (Array.isArray(payload?.results)) {
    return payload.results
  }

  if (Array.isArray(payload?.rows)) {
    return payload.rows
  }

  return []
}

function normalizeSale(row) {
  return {
    id: row.id ?? row.sale_id ?? row.pk ?? '',
    receipt_number: row.receipt_number ?? row.receipt ?? '',
    cashier_username:
      row.cashier_username ??
      row.cashier?.username ??
      row.cashier_name ??
      '',
    warehouse_name:
      row.warehouse_name ??
      row.warehouse?.name ??
      '',
    shift_id: row.shift_id ?? row.shift ?? '',
    payment_method: row.payment_method ?? '',
    total_amount: row.total_amount ?? row.total ?? 0,
    total_cost: row.total_cost ?? row.cost ?? 0,
    total_profit: row.total_profit ?? row.profit ?? 0,
    terminal_id: row.terminal_id ?? '',
    terminal_name: row.terminal_name ?? '',
    created_at: row.created_at ?? row.date ?? row.timestamp ?? '',
  }
}

export default function SalesPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [sales, setSales] = useState([])

  const [search, setSearch] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const fetchFromKnownEndpoints = async (queryString) => {
    const endpoints = [
      `/sales/${queryString}`,
      `/sales/history/${queryString}`,
      `/sales/sales/${queryString}`,
    ]

    let lastError = null

    for (const endpoint of endpoints) {
      try {
        const response = await API.get(endpoint)
        const parsed = parseSalesPayload(response.data).map(normalizeSale)

        if (Array.isArray(parsed)) {
          return parsed
        }
      } catch (err) {
        lastError = err
      }
    }

    throw lastError || new Error('No sales endpoint responded.')
  }

  const loadSales = async () => {
    try {
      setLoading(true)
      setError('')

      const params = new URLSearchParams()
      if (search.trim()) params.append('search', search.trim())
      if (paymentMethod) params.append('payment_method', paymentMethod)
      if (dateFrom) params.append('date_from', dateFrom)
      if (dateTo) params.append('date_to', dateTo)

      const queryString = params.toString() ? `?${params.toString()}` : ''
      const parsedSales = await fetchFromKnownEndpoints(queryString)

      setSales(parsedSales)
    } catch (err) {
      const backendMessage =
        err?.response?.data?.detail ||
        err?.response?.data?.error ||
        err?.message ||
        'Could not load sales.'
      setError(backendMessage)
      setSales([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSales()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const filteredSales = useMemo(() => {
    return sales.filter((row) => {
      const haystack = [
        row.receipt_number,
        row.cashier_username,
        row.warehouse_name,
        row.payment_method,
        row.terminal_id,
        row.terminal_name,
      ]
        .join(' ')
        .toLowerCase()

      const matchesSearch = search.trim()
        ? haystack.includes(search.trim().toLowerCase())
        : true

      const matchesPayment = paymentMethod
        ? String(row.payment_method || '').toLowerCase() === paymentMethod.toLowerCase()
        : true

      const rowDate = row.created_at ? String(row.created_at).slice(0, 10) : ''
      const matchesFrom = dateFrom ? rowDate >= dateFrom : true
      const matchesTo = dateTo ? rowDate <= dateTo : true

      return matchesSearch && matchesPayment && matchesFrom && matchesTo
    })
  }, [sales, search, paymentMethod, dateFrom, dateTo])

  const summary = useMemo(() => {
    return filteredSales.reduce(
      (acc, row) => {
        acc.count += 1
        acc.totalAmount += Number(row.total_amount || 0)
        acc.totalCost += Number(row.total_cost || 0)
        acc.totalProfit += Number(row.total_profit || 0)

        if (String(row.payment_method || '').toLowerCase() === 'cash') {
          acc.cashCount += 1
        } else if (String(row.payment_method || '').trim()) {
          acc.nonCashCount += 1
        }

        return acc
      },
      {
        count: 0,
        totalAmount: 0,
        totalCost: 0,
        totalProfit: 0,
        cashCount: 0,
        nonCashCount: 0,
      }
    )
  }, [filteredSales])

  return (
    <div>
      <div className="section-header">
        <h2>Sales</h2>
        <p className="muted-text">
          Review sales activity, amounts, profit, and open receipt detail.
        </p>
      </div>

      <div className="content-card" style={{ marginTop: '18px' }}>
        <h3>Filters</h3>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '12px' }}>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search receipt, cashier, warehouse"
          />

          <select
            value={paymentMethod}
            onChange={(e) => setPaymentMethod(e.target.value)}
          >
            <option value="">All Payments</option>
            <option value="cash">Cash</option>
            <option value="card">Card</option>
            <option value="ecocash">EcoCash</option>
            <option value="bank_transfer">Bank Transfer</option>
          </select>

          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />

          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />

          <button
            type="button"
            className="btn btn-secondary"
            onClick={loadSales}
          >
            Reload
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              setSearch('')
              setPaymentMethod('')
              setDateFrom('')
              setDateTo('')
            }}
          >
            Clear Filters
          </button>
        </div>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading sales...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}

      <div className="stats-grid" style={{ marginTop: '18px' }}>
        <div className="stat-card">
          <span>Sales Count</span>
          <strong>{summary.count}</strong>
        </div>
        <div className="stat-card">
          <span>Total Revenue</span>
          <strong>£{money(summary.totalAmount)}</strong>
        </div>
        <div className="stat-card">
          <span>Total Cost</span>
          <strong>£{money(summary.totalCost)}</strong>
        </div>
        <div className="stat-card">
          <span>Total Profit</span>
          <strong>£{money(summary.totalProfit)}</strong>
        </div>
        <div className="stat-card">
          <span>Cash Sales</span>
          <strong>{summary.cashCount}</strong>
        </div>
        <div className="stat-card">
          <span>Non-Cash Sales</span>
          <strong>{summary.nonCashCount}</strong>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Sales Register</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Receipt</th>
                <th>Cashier</th>
                <th>Warehouse</th>
                <th>Shift</th>
                <th>Payment</th>
                <th>Total</th>
                <th>Profit</th>
                <th>Created</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredSales.map((row) => (
                <tr key={row.id}>
                  <td>{safeText(row.id)}</td>
                  <td>{safeText(row.receipt_number)}</td>
                  <td>{safeText(row.cashier_username)}</td>
                  <td>{safeText(row.warehouse_name)}</td>
                  <td>{safeText(row.shift_id)}</td>
                  <td>{safeText(row.payment_method)}</td>
                  <td>£{money(row.total_amount)}</td>
                  <td>£{money(row.total_profit)}</td>
                  <td>{safeText(row.created_at)}</td>
                  <td>
                    {row.id ? (
                      <Link to={`/sales/${row.id}`} className="btn btn-secondary">
                        Open
                      </Link>
                    ) : (
                      '-'
                    )}
                  </td>
                </tr>
              ))}

              {filteredSales.length === 0 ? (
                <tr>
                  <td colSpan="10">No sales found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}