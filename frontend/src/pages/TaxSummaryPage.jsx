import { useEffect, useState } from 'react'
import API from '../api/client'

function money(value) {
  return new Intl.NumberFormat('en-GB', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value || 0))
}

function todayString() {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

export default function TaxSummaryPage() {
  const [dateFrom, setDateFrom] = useState(todayString())
  const [dateTo, setDateTo] = useState(todayString())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState(null)

  const loadSummary = async () => {
    try {
      setLoading(true)
      setError('')

      const response = await API.get(
        `/finance/tax-summary/?date_from=${dateFrom}&date_to=${dateTo}`
      )

      setData(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load tax summary.')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSummary()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const summary = data?.summary || {}

  return (
    <div>
      <div className="section-header">
        <h2>VAT Summary</h2>
        <p className="muted-text">
          Review output tax from sales, input tax from supplier invoices, and net VAT payable.
        </p>
      </div>

      <div className="content-card" style={{ marginTop: '18px' }}>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          <button type="button" className="btn btn-secondary" onClick={loadSummary}>
            Load
          </button>
        </div>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading VAT summary...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}

      {!loading && !error ? (
        <>
          <div className="stats-grid" style={{ marginTop: '18px' }}>
            <div className="stat-card">
              <span>Sales Count</span>
              <strong>{summary.sales_count || 0}</strong>
            </div>
            <div className="stat-card">
              <span>Purchase Invoices</span>
              <strong>{summary.purchase_invoice_count || 0}</strong>
            </div>
            <div className="stat-card">
              <span>Output Net Sales</span>
              <strong>£{money(summary.output_net_sales)}</strong>
            </div>
            <div className="stat-card">
              <span>Output Tax</span>
              <strong>£{money(summary.output_tax)}</strong>
            </div>
            <div className="stat-card">
              <span>Output Gross Sales</span>
              <strong>£{money(summary.output_gross_sales)}</strong>
            </div>
            <div className="stat-card">
              <span>Input Net Purchases</span>
              <strong>£{money(summary.input_net_purchases)}</strong>
            </div>
            <div className="stat-card">
              <span>Input Tax</span>
              <strong>£{money(summary.input_tax)}</strong>
            </div>
            <div className="stat-card">
              <span>Input Gross Purchases</span>
              <strong>£{money(summary.input_gross_purchases)}</strong>
            </div>
          </div>

          <div className="content-card" style={{ marginTop: '20px' }}>
            <h3>Net VAT Position</h3>
            <div style={{ marginTop: '12px', fontSize: '22px', fontWeight: 700 }}>
              £{money(summary.net_vat_payable)}
            </div>
            <p className="muted-text" style={{ marginTop: '8px' }}>
              Positive means VAT payable. Negative means input tax exceeds output tax for the selected period.
            </p>
          </div>
        </>
      ) : null}
    </div>
  )
}