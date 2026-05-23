import { useEffect, useState } from 'react'
import API from '../api/client'

function money(value) {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0.00'
  return num.toFixed(2)
}

export default function RefundsPage() {
  const [saleId, setSaleId] = useState('')
  const [sale, setSale] = useState(null)
  const [refunds, setRefunds] = useState([])
  const [reason, setReason] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('cash')
  const [items, setItems] = useState([])

  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadRefunds = async () => {
    const { data } = await API.get('/sales/refunds/')
    setRefunds(Array.isArray(data) ? data : [])
  }

  useEffect(() => {
    loadRefunds().catch(() => {})
  }, [])

  const loadSale = async () => {
    try {
      setLoading(true)
      setError('')
      setSuccess('')
      setSale(null)
      setItems([])

      if (!saleId) {
        setError('Enter a sale ID.')
        return
      }

      const { data } = await API.get(`/sales/${saleId}/`)
      setSale(data)

      const saleItems = Array.isArray(data.items) ? data.items : []

      setItems(
        saleItems.map((item) => ({
          sale_item: item.id,
          product_name: item.product_name,
          product_sku: item.product_sku,
          quantity_sold: Number(item.quantity || 0),
          refund_quantity: 0,
          unit_price: item.unit_price,
          tax_amount: item.tax_amount,
          line_total: item.line_total,
        }))
      )
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load sale.')
    } finally {
      setLoading(false)
    }
  }

  const updateRefundQuantity = (saleItemId, value) => {
    const qty = Math.max(Number(value || 0), 0)

    setItems((prev) =>
      prev.map((item) =>
        item.sale_item === saleItemId
          ? {
              ...item,
              refund_quantity: Math.min(qty, item.quantity_sold),
            }
          : item
      )
    )
  }

  const submitRefund = async () => {
    try {
      setSubmitting(true)
      setError('')
      setSuccess('')

      const refundItems = items
        .filter((item) => Number(item.refund_quantity || 0) > 0)
        .map((item) => ({
          sale_item: item.sale_item,
          quantity: Number(item.refund_quantity),
        }))

      if (!sale?.id) {
        setError('Load a sale before creating a refund.')
        return
      }

      if (refundItems.length === 0) {
        setError('Enter at least one refund quantity.')
        return
      }

      const { data } = await API.post('/sales/refunds/', {
        sale: sale.id,
        payment_method: paymentMethod,
        reason,
        returned_to_stock: true,
        items: refundItems,
      })

      setSuccess(data.detail || 'Refund completed successfully.')
      setReason('')
      setItems([])
      setSale(null)
      setSaleId('')
      await loadRefunds()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create refund.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="section-header">
        <h2>Refunds / Returns</h2>
        <p className="muted-text">
          Create controlled refunds, return stock, reverse tax, and maintain audit history.
        </p>
      </div>

      <div className="content-card" style={{ marginTop: '18px' }}>
        <h3>Find Sale</h3>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '12px' }}>
          <input
            type="number"
            value={saleId}
            onChange={(e) => setSaleId(e.target.value)}
            placeholder="Enter Sale ID"
          />

          <button type="button" className="btn btn-secondary" onClick={loadSale} disabled={loading}>
            {loading ? 'Loading...' : 'Load Sale'}
          </button>
        </div>
      </div>

      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}
      {success ? <p style={{ color: 'green', marginTop: '16px' }}>{success}</p> : null}

      {sale ? (
        <div className="content-card" style={{ marginTop: '20px' }}>
          <h3>Sale Details</h3>

          <p><strong>Receipt:</strong> {sale.receipt_number}</p>
          <p><strong>Warehouse:</strong> {sale.warehouse_name}</p>
          <p><strong>Total:</strong> £{money(sale.total_amount)}</p>
          <p><strong>Tax:</strong> £{money(sale.tax_amount)}</p>

          <label style={{ marginTop: '12px', display: 'block' }}>Refund Payment Method</label>
          <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
            <option value="cash">Cash</option>
            <option value="card">Card</option>
            <option value="ecocash">EcoCash</option>
            <option value="bank">Bank</option>
            <option value="store_credit">Store Credit</option>
          </select>

          <label style={{ marginTop: '12px', display: 'block' }}>Reason</label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Reason for refund / return"
            rows="3"
            style={{ width: '100%' }}
          />

          <div className="table-wrap" style={{ marginTop: '12px' }}>
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>SKU</th>
                  <th>Sold Qty</th>
                  <th>Refund Qty</th>
                  <th>Unit Price</th>
                  <th>Original Tax</th>
                  <th>Original Line Total</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.sale_item}>
                    <td>{item.product_name}</td>
                    <td>{item.product_sku}</td>
                    <td>{item.quantity_sold}</td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        max={item.quantity_sold}
                        value={item.refund_quantity}
                        onChange={(e) => updateRefundQuantity(item.sale_item, e.target.value)}
                        style={{ width: '90px' }}
                      />
                    </td>
                    <td>£{money(item.unit_price)}</td>
                    <td>£{money(item.tax_amount)}</td>
                    <td>£{money(item.line_total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <button
            type="button"
            className="btn btn-danger"
            style={{ marginTop: '16px' }}
            onClick={submitRefund}
            disabled={submitting}
          >
            {submitting ? 'Processing...' : 'Create Refund'}
          </button>
        </div>
      ) : null}

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Refund History</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Refund No.</th>
                <th>Receipt</th>
                <th>Cashier</th>
                <th>Method</th>
                <th>Tax Reversed</th>
                <th>Total Refunded</th>
                <th>Profit Reversed</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {refunds.map((refund) => (
                <tr key={refund.id}>
                  <td>{refund.refund_number}</td>
                  <td>{refund.receipt_number}</td>
                  <td>{refund.cashier_username || '-'}</td>
                  <td>{refund.payment_method}</td>
                  <td>£{money(refund.tax_amount)}</td>
                  <td>£{money(refund.total_amount)}</td>
                  <td>£{money(refund.total_profit_reversed)}</td>
                  <td>{refund.created_at}</td>
                </tr>
              ))}

              {refunds.length === 0 ? (
                <tr>
                  <td colSpan="8">No refunds found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}