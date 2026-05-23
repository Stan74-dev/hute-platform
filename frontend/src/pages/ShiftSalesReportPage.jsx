import { useEffect, useState } from 'react'
import API from '../api/client'

function formatMoney(value) {
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

export default function ShiftSalesReportPage() {
  const [data, setData] = useState(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [dateFilter, setDateFilter] = useState('')
  const [shiftFilter, setShiftFilter] = useState('')

  const buildQuery = () => {
    const params = new URLSearchParams()

    if (dateFilter) {
      params.append('date', dateFilter)
    }

    if (shiftFilter) {
      params.append('shift', shiftFilter)
    }

    return params.toString()
  }

  const loadReport = async () => {
    try {
      setLoading(true)
      setError('')
      setSuccess('')

      const query = buildQuery()

      const url = query
        ? `/accounts/shift/sales-report/?${query}`
        : '/accounts/shift/sales-report/'

      const response = await API.get(url)

      setData(response.data || {})
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Could not load shift sales report.'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadReport()
  }, [])

  const downloadBlob = (blobData, filename) => {
    const url = window.URL.createObjectURL(new Blob([blobData]))

    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)

    document.body.appendChild(link)
    link.click()
    link.remove()

    window.URL.revokeObjectURL(url)
  }

  const exportPdf = async () => {
    try {
      setError('')
      setSuccess('')

      const query = buildQuery()

      const url = query
        ? `/accounts/shift/report/pdf/?${query}`
        : '/accounts/shift/report/pdf/'

      const response = await API.get(url, {
        responseType: 'blob',
      })

      downloadBlob(response.data, 'shift_sales_report.pdf')

      setSuccess('PDF report downloaded.')
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Could not export PDF.'
      )
    }
  }

  const summary = data?.summary || {}

  const rows =
    data?.sales ||
    data?.results ||
    data?.rows ||
    []

  return (
    <div>
      <div className="section-header">
        <h2>Shift Sales Report</h2>

        <p className="muted-text">
          Revenue, transactions, and profit by shift.
        </p>
      </div>

      <div
        className="content-card"
        style={{ marginTop: '18px' }}
      >
        <h3>Filters</h3>

        <div
          style={{
            display: 'flex',
            gap: '10px',
            flexWrap: 'wrap',
            marginTop: '12px',
          }}
        >
          <input
            type="date"
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
          />

          <input
            type="text"
            value={shiftFilter}
            onChange={(e) => setShiftFilter(e.target.value)}
            placeholder="Shift ID"
          />

          <button
            type="button"
            className="btn btn-secondary"
            onClick={loadReport}
          >
            Apply Filters
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              setDateFilter('')
              setShiftFilter('')
            }}
          >
            Clear
          </button>

          <button
            type="button"
            className="btn btn-primary"
            onClick={exportPdf}
          >
            Export PDF
          </button>
        </div>
      </div>

      {loading ? (
        <p style={{ marginTop: '16px' }}>
          Loading shift sales report...
        </p>
      ) : null}

      {error ? (
        <p
          className="error-text"
          style={{ marginTop: '16px' }}
        >
          {error}
        </p>
      ) : null}

      {success ? (
        <p
          style={{
            color: 'green',
            marginTop: '16px',
          }}
        >
          {success}
        </p>
      ) : null}

      <div
        className="stats-grid"
        style={{ marginTop: '18px' }}
      >
        <div className="stat-card">
          <span>Transactions</span>

          <strong>
            {summary.transactions || 0}
          </strong>
        </div>

        <div className="stat-card">
          <span>Items Sold</span>

          <strong>
            {summary.items_sold || 0}
          </strong>
        </div>

        <div className="stat-card">
          <span>Total Revenue</span>

          <strong>
            £{formatMoney(summary.total_amount)}
          </strong>
        </div>

        <div className="stat-card">
          <span>Sales Tax / VAT</span>

          <strong>
            £{formatMoney(summary.tax_amount)}
          </strong>
        </div>

        <div className="stat-card">
          <span>Total Profit</span>

          <strong>
            £{formatMoney(summary.total_profit)}
          </strong>
        </div>
      </div>

      <div
        className="content-card"
        style={{ marginTop: '20px' }}
      >
        <h3>Sales Register</h3>

        <div
          className="table-wrap"
          style={{ marginTop: '12px' }}
        >
          <table>
            <thead>
              <tr>
                <th>Receipt</th>
                <th>Cashier</th>
                <th>Warehouse</th>
                <th>Shift</th>
                <th>Payment</th>
                <th>Total</th>
                <th>Sales Tax / VAT</th>
                <th>Profit</th>
                <th>Created</th>
                <th>Terminal</th>
              </tr>
            </thead>

            <tbody>
              {rows.map((row, index) => (
                <tr key={row.id || index}>
                  <td>{row.receipt_number}</td>

                  <td>
                    {row.cashier_username || '-'}
                  </td>

                  <td>
                    {row.warehouse_name || '-'}
                  </td>

                  <td>{row.shift || '-'}</td>

                  <td>
                    {row.payment_method || '-'}
                  </td>

                  <td>
                    £{formatMoney(row.total_amount)}
                  </td>

                  <td>
                    £{formatMoney(row.tax_amount || row.tax)}
                  </td>

                  <td>
                    £{formatMoney(row.profit || row.total_profit)}
                  </td>

                  <td>
                    {formatDate(row.created_at)}
                  </td>

                  <td>
                    {row.terminal_name || '-'}
                  </td>
                </tr>
              ))}

              {rows.length === 0 ? (
                <tr>
                  <td colSpan="10">
                    No shift sales data found.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}