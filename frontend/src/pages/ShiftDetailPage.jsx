import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import API from '../api/client'

function money(value) {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0.00'
  return num.toFixed(2)
}

export default function ShiftDetailPage() {
  const { shiftId } = useParams()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState(null)

  const loadShift = async () => {
    try {
      setLoading(true)
      setError('')

      const [detailRes, shiftsRes] = await Promise.all([
        API.get(`/accounts/shift/detail/${shiftId}/`),
        API.get('/accounts/shifts/all/'),
      ])

      const shifts = shiftsRes.data?.rows || shiftsRes.data?.results || shiftsRes.data?.history || []
      const shift = shifts.find((row) => String(row.id || row.shift_id) === String(shiftId)) || { id: shiftId, shift_id: shiftId }

      setData({ shift, summary: detailRes.data?.summary || {}, sales: detailRes.data?.sales || detailRes.data?.results || [] })
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load shift detail.')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadShift()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shiftId])

  const exportPdf = async () => {
    try {
      const { data: payload } = await API.get(`/accounts/shift/report-pdf/?shift=${shiftId}`)
      console.log('Shift report payload:', payload)
      alert('Shift report payload prepared.')
    } catch (err) {
      alert(err.response?.data?.detail || 'Could not prepare shift report.')
    }
  }

  if (loading) return <p>Loading shift detail...</p>
  if (error) return <p className="error-text">{error}</p>
  if (!data?.shift) return <p>Shift not found.</p>

  const shift = data.shift
  const summary = data.summary || {}
  const sales = data.sales || []

  return (
    <div>
      <div className="section-header"><h2>Shift Detail</h2><p className="muted-text">Full-screen investigation view for shift #{shift.id || shift.shift_id}.</p></div>
      <div style={{ marginTop: '12px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <Link to="/day-detail" className="btn btn-secondary">Day Investigation</Link>
        <button type="button" className="btn btn-secondary" onClick={() => navigate(-1)}>Go Back</button>
        <button type="button" className="btn btn-primary" onClick={exportPdf}>Export PDF</button>
      </div>
      <div className="card-grid" style={{ marginTop: '20px' }}>
        <div className="content-card"><h3>Shift Overview</h3><div style={{ marginTop: '12px' }}>
          <p><strong>ID:</strong> {shift.id || shift.shift_id}</p><p><strong>Cashier:</strong> {shift.cashier_username || shift.cashier || '-'}</p><p><strong>Terminal:</strong> {shift.terminal_id || shift.terminal || shift.terminal_name || '-'}</p><p><strong>Status:</strong> {shift.status || '-'}</p><p><strong>Opened At:</strong> {shift.opened_at || shift.opened || '-'}</p><p><strong>Closed At:</strong> {shift.closed_at || shift.closed || '-'}</p><p><strong>Opening Float:</strong> £{money(shift.opening_float)}</p><p><strong>Cash Sales:</strong> £{money(shift.cash_sales)}</p><p><strong>Card Sales:</strong> £{money(shift.card_sales)}</p><p><strong>Expected Cash:</strong> £{money(shift.expected_cash)}</p><p><strong>Actual Cash:</strong> £{money(shift.actual_cash)}</p><p><strong>Variance:</strong> £{money(shift.variance)}</p>
        </div></div>
        <div className="content-card"><h3>Shift Summary</h3><div style={{ marginTop: '12px' }}><p><strong>Sales Count:</strong> {summary.sales_count || summary.transactions || 0}</p><p><strong>Items Sold:</strong> {summary.items_sold || summary.total_quantity || 0}</p><p><strong>Total Sales Amount:</strong> £{money(summary.total_sales || summary.total_amount)}</p><p><strong>Total Sales Profit:</strong> £{money(summary.total_profit)}</p><p><strong>Cash Sales:</strong> £{money(summary.cash_sales)}</p><p><strong>Card Sales:</strong> £{money(summary.card_sales)}</p></div></div>
      </div>
      <div className="content-card" style={{ marginTop: '20px' }}><h3>Related Sales</h3><div className="table-wrap" style={{ marginTop: '12px' }}><table><thead><tr><th>Receipt</th><th>Cashier</th><th>Warehouse</th><th>Payment</th><th>Total</th><th>Profit</th><th>Created</th><th>Action</th></tr></thead><tbody>{sales.map((row, index) => (<tr key={row.id || row.sale_id || row.receipt_number || index}><td>{row.receipt_number || row.receipt || '-'}</td><td>{row.cashier_username || row.cashier || '-'}</td><td>{row.warehouse_name || row.warehouse || '-'}</td><td>{row.payment_method || row.payment || '-'}</td><td>£{money(row.total_amount || row.total)}</td><td>£{money(row.total_profit || row.profit)}</td><td>{row.created_at || row.created || '-'}</td><td><Link to={`/sales/${row.id || row.sale_id}`} className="btn btn-secondary">Open Sale</Link></td></tr>))}{sales.length === 0 ? <tr><td colSpan="8">No related sales found.</td></tr> : null}</tbody></table></div></div>
    </div>
  )
}
