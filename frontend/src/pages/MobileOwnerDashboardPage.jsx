import { useEffect, useState } from 'react'
import API from '../api/client'

function money(v) { return Number(v || 0).toFixed(2) }

export default function MobileOwnerDashboardPage() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    API.get('/reports/owner-mobile-dashboard/')
      .then((res) => setData(res.data))
      .catch(() => setError('Could not load owner dashboard.'))
  }, [])

  return (
    <div>
      <h2>Owner Mobile Dashboard</h2>
      {error ? <div className="alert alert-error">{error}</div> : null}
      {!data ? <p>Loading...</p> : (
        <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
          <div className="content-card"><span>Total Sales</span><h2>£{money(data.total_sales)}</h2></div>
          <div className="content-card"><span>Transactions</span><h2>{data.transaction_count}</h2></div>
          <div className="content-card"><span>Cash Sales</span><h2>£{money(data.cash_sales)}</h2></div>
          <div className="content-card"><span>Card Sales</span><h2>£{money(data.card_sales)}</h2></div>
          <div className="content-card"><span>Gross Profit</span><h2>£{money(data.total_profit)}</h2></div>
          <div className="content-card"><span>Refunds</span><h2>£{money(data.refunds_total)}</h2></div>
          <div className="content-card"><span>Anomalies</span><h2>{data.anomalies_count}</h2></div>
        </div>
      )}
    </div>
  )
}
