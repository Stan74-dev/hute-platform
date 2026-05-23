import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import API from '../api/client'

function money(value) {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0.00'
  return num.toFixed(2)
}

export default function SaleDetailPage() {
  const { saleId } = useParams()
  const [sale, setSale] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadSale = async () => {
    try {
      setLoading(true)
      setError('')
      const { data } = await API.get(`/sales/${saleId}/`)
      setSale(data || null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load sale.')
      setSale(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSale()
  }, [saleId])

  if (loading) {
    return <p>Loading sale...</p>
  }

  if (error) {
    return <p className="error-text">{error}</p>
  }

  if (!sale) {
    return <p>No sale found.</p>
  }

  return (
    <div>
      <div className="section-header">
        <h2>Sale Detail</h2>
        <p className="muted-text">
          Receipt {sale.receipt_number}
        </p>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <div className="table-wrap">
          <table>
            <tbody>
              <tr><th>Receipt Number</th><td>{sale.receipt_number}</td></tr>
              <tr><th>Warehouse</th><td>{sale.warehouse_name || '-'}</td></tr>
              <tr><th>Cashier</th><td>{sale.cashier_username || '-'}</td></tr>
              <tr><th>Payment Method</th><td>{sale.payment_method}</td></tr>
              <tr><th>Subtotal</th><td>£{money(sale.subtotal_amount)}</td></tr>
              <tr><th>Tax</th><td>£{money(sale.tax_amount)}</td></tr>
              <tr><th>Total</th><td>£{money(sale.total_amount)}</td></tr>
              <tr><th>Created At</th><td>{sale.created_at}</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Items</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>SKU</th>
                <th>Qty</th>
                <th>Unit Price</th>
                <th>Tax</th>
                <th>Line Total</th>
              </tr>
            </thead>
            <tbody>
              {(sale.items || []).map((item) => (
                <tr key={item.id}>
                  <td>{item.product_name || '-'}</td>
                  <td>{item.product_sku || '-'}</td>
                  <td>{item.quantity}</td>
                  <td>£{money(item.unit_price)}</td>
                  <td>£{money(item.tax_amount)}</td>
                  <td>£{money(item.line_total)}</td>
                </tr>
              ))}
              {(sale.items || []).length === 0 ? (
                <tr><td colSpan="6">No sale items found.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Batch Allocations (FEFO)</h3>

        {(sale.items || []).map((item) => (
          <div key={`alloc-${item.id}`} style={{ marginTop: '16px' }}>
            <div style={{ fontWeight: 700, marginBottom: '8px' }}>
              {item.product_name} ({item.product_sku})
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Batch Number</th>
                    <th>Expiry Date</th>
                    <th>Allocated Qty</th>
                  </tr>
                </thead>
                <tbody>
                  {(item.batch_allocations || []).map((allocation) => (
                    <tr key={allocation.id}>
                      <td>{allocation.batch_number || '-'}</td>
                      <td>{allocation.expiry_date || '-'}</td>
                      <td>{allocation.quantity_allocated}</td>
                    </tr>
                  ))}
                  {(item.batch_allocations || []).length === 0 ? (
                    <tr><td colSpan="3">No batch allocations found.</td></tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}