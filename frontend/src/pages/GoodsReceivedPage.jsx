import { useEffect, useMemo, useState } from 'react'
import API from '../api/client'

function money(value) {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0.00'
  return num.toFixed(2)
}

function numberValue(value) {
  const num = Number(value || 0)
  return Number.isNaN(num) ? 0 : num
}

function isReceivableStatus(status) {
  return ['submitted', 'partial'].includes(String(status || '').toLowerCase())
}

function todayPlusMonths(months) {
  const d = new Date()
  d.setMonth(d.getMonth() + months)
  return d.toISOString().slice(0, 10)
}

export default function GoodsReceivedPage() {
  const [purchaseOrders, setPurchaseOrders] = useState([])
  const [grns, setGrns] = useState([])
  const [selectedPoId, setSelectedPoId] = useState('')
  const [receiveItems, setReceiveItems] = useState([])
  const [notes, setNotes] = useState('')

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadData = async () => {
    try {
      setLoading(true)
      setError('')
      setSuccess('')

      const [poRes, grnRes] = await Promise.all([
        API.get('/inventory/purchase-orders/'),
        API.get('/inventory/grns/'),
      ])

      const poRows = Array.isArray(poRes.data) ? poRes.data : []
      const grnRows = Array.isArray(grnRes.data) ? grnRes.data : []

      setPurchaseOrders(poRows)
      setGrns(grnRows)

      const receivable = poRows.filter(
        (po) => isReceivableStatus(po.status) && numberValue(po.pending_quantity_total) > 0
      )

      if (receivable.length > 0) {
        const stillExists = receivable.find((po) => String(po.id) === String(selectedPoId))
        if (!stillExists) {
          setSelectedPoId(String(receivable[0].id))
        }
      } else {
        setSelectedPoId('')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load goods receiving data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const receivablePurchaseOrders = useMemo(() => {
    return purchaseOrders.filter(
      (po) => isReceivableStatus(po.status) && numberValue(po.pending_quantity_total) > 0
    )
  }, [purchaseOrders])

  const selectedPo = useMemo(() => {
    return receivablePurchaseOrders.find((po) => String(po.id) === String(selectedPoId)) || null
  }, [receivablePurchaseOrders, selectedPoId])

  useEffect(() => {
    if (!selectedPo) {
      setReceiveItems([])
      return
    }

    setReceiveItems(
      (selectedPo.items || []).map((item) => ({
        purchase_order_item: item.id,
        product: item.product,
        product_name: item.product_name,
        product_sku: item.product_sku,
        ordered_quantity: numberValue(item.quantity),
        received_quantity: numberValue(item.received_quantity),
        pending_quantity: numberValue(item.pending_quantity),
        unit_cost: numberValue(item.unit_cost),
        quantity_received: 0,
        batch_number: `BATCH-${selectedPo.po_number || selectedPo.id}-${item.id}`,
        expiry_date: todayPlusMonths(12),
      }))
    )
  }, [selectedPo])

  const updateReceiveQty = (purchaseOrderItemId, value) => {
    const qty = Math.max(0, numberValue(value))

    setReceiveItems((prev) =>
      prev.map((item) => {
        if (item.purchase_order_item !== purchaseOrderItemId) return item
        return {
          ...item,
          quantity_received: Math.min(qty, item.pending_quantity),
        }
      })
    )
  }

  const updateItemField = (purchaseOrderItemId, field, value) => {
    setReceiveItems((prev) =>
      prev.map((item) => {
        if (item.purchase_order_item !== purchaseOrderItemId) return item
        return {
          ...item,
          [field]: value,
        }
      })
    )
  }

  const submitGrn = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!selectedPo) {
      setError('Select a purchase order.')
      return
    }

    const items = receiveItems
      .map((item) => ({
        purchase_order_item: item.purchase_order_item,
        product: item.product,
        quantity_received: numberValue(item.quantity_received),
        batch_number: String(item.batch_number || '').trim(),
        expiry_date: item.expiry_date || null,
        unit_cost: numberValue(item.unit_cost),
      }))
      .filter((item) => item.quantity_received > 0)

    if (items.length === 0) {
      setError('Enter at least one quantity to receive.')
      return
    }

    const missingBatch = items.find((item) => !item.batch_number)
    if (missingBatch) {
      setError('Every received item must have a batch number.')
      return
    }

    const missingExpiry = items.find((item) => !item.expiry_date)
    if (missingExpiry) {
      setError('Every received item must have an expiry date.')
      return
    }

    try {
      setSubmitting(true)

      const payload = {
        purchase_order: Number(selectedPo.id),
        notes,
        items,
      }

      const { data } = await API.post('/inventory/grns/', payload)

      setSuccess(data?.detail || 'Goods received successfully.')
      setNotes('')
      await loadData()
    } catch (err) {
      const responseData = err.response?.data

      if (typeof responseData === 'string') {
        setError(responseData)
      } else if (responseData?.detail) {
        setError(responseData.detail)
      } else if (responseData?.error) {
        setError(responseData.error)
      } else if (responseData) {
        setError(JSON.stringify(responseData))
      } else {
        setError('Could not receive goods.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="section-header">
        <h2>Goods Received</h2>
        <p className="muted-text">
          Select a purchase order, enter received quantities, batch numbers, expiry dates, and post a GRN.
        </p>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading GRN data...</p> : null}

      {error ? (
        <p className="error-text" style={{ marginTop: '16px' }}>
          {error}
        </p>
      ) : null}

      {success ? (
        <p style={{ marginTop: '16px', color: 'green' }}>
          {success}
        </p>
      ) : null}

      <div className="card-grid" style={{ marginTop: '20px' }}>
        <div className="content-card">
          <h3>Receivable Purchase Orders</h3>

          <div style={{ display: 'grid', gap: '10px', marginTop: '12px' }}>
            {receivablePurchaseOrders.map((po) => {
              const isSelected = String(po.id) === String(selectedPoId)

              return (
                <button
                  key={po.id}
                  type="button"
                  onClick={() => setSelectedPoId(String(po.id))}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    padding: '14px',
                    borderRadius: '12px',
                    border: isSelected ? '3px solid #2563eb' : '1px solid #cbd5e1',
                    background: isSelected ? '#dbeafe' : '#ffffff',
                    boxShadow: isSelected ? '0 0 0 2px rgba(37, 99, 235, 0.18)' : 'none',
                    cursor: 'pointer',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      gap: '12px',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700 }}>
                        {po.po_number} - {po.supplier_name || '-'}
                      </div>
                      <div style={{ fontSize: '13px', color: '#475569', marginTop: '4px' }}>
                        Warehouse: {po.warehouse_name || '-'}
                      </div>
                    </div>

                    <div
                      style={{
                        padding: '5px 10px',
                        borderRadius: '999px',
                        background: isSelected ? '#2563eb' : '#e2e8f0',
                        color: isSelected ? '#ffffff' : '#334155',
                        fontSize: '12px',
                        fontWeight: 700,
                      }}
                    >
                      {isSelected ? 'SELECTED' : String(po.status || '-').toUpperCase()}
                    </div>
                  </div>

                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
                      gap: '10px',
                      marginTop: '12px',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>Ordered</div>
                      <div style={{ fontWeight: 700 }}>{numberValue(po.ordered_quantity_total)}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>Received</div>
                      <div style={{ fontWeight: 700 }}>{numberValue(po.received_quantity_total)}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>Pending</div>
                      <div style={{ fontWeight: 700 }}>{numberValue(po.pending_quantity_total)}</div>
                    </div>
                  </div>
                </button>
              )
            })}

            {receivablePurchaseOrders.length === 0 ? (
              <div className="content-card" style={{ marginTop: '4px' }}>
                No receivable purchase orders found.
              </div>
            ) : null}
          </div>
        </div>

        <div className="content-card">
          <h3>Receive Goods</h3>

          {selectedPo ? (
            <form onSubmit={submitGrn}>
              <div className="table-wrap" style={{ marginTop: '12px' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Ordered</th>
                      <th>Received</th>
                      <th>Pending</th>
                      <th>Receive Now</th>
                      <th>Batch Number</th>
                      <th>Expiry Date</th>
                      <th>Unit Cost</th>
                      <th>Line Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {receiveItems.map((item) => (
                      <tr key={item.purchase_order_item}>
                        <td>
                          {item.product_name || '-'} ({item.product_sku || '-'})
                        </td>
                        <td>{item.ordered_quantity}</td>
                        <td>{item.received_quantity}</td>
                        <td>{item.pending_quantity}</td>
                        <td>
                          <input
                            type="number"
                            min="0"
                            max={item.pending_quantity}
                            value={item.quantity_received}
                            onChange={(e) =>
                              updateReceiveQty(item.purchase_order_item, e.target.value)
                            }
                            style={{ width: '90px' }}
                          />
                        </td>
                        <td>
                          <input
                            type="text"
                            value={item.batch_number}
                            onChange={(e) =>
                              updateItemField(
                                item.purchase_order_item,
                                'batch_number',
                                e.target.value
                              )
                            }
                            placeholder="Batch number"
                            style={{ width: '150px' }}
                          />
                        </td>
                        <td>
                          <input
                            type="date"
                            value={item.expiry_date}
                            onChange={(e) =>
                              updateItemField(
                                item.purchase_order_item,
                                'expiry_date',
                                e.target.value
                              )
                            }
                            style={{ width: '145px' }}
                          />
                        </td>
                        <td>£{money(item.unit_cost)}</td>
                        <td>£{money(item.unit_cost * item.quantity_received)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <label style={{ display: 'block', marginTop: '14px' }}>
                Notes
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows="3"
                  placeholder="Optional receiving notes"
                  style={{ width: '100%', marginTop: '6px' }}
                />
              </label>

              <button
                type="submit"
                className="primary"
                disabled={submitting}
                style={{ marginTop: '14px' }}
              >
                {submitting ? 'Posting GRN...' : 'Receive Goods'}
              </button>
            </form>
          ) : (
            <p className="muted-text" style={{ marginTop: '12px' }}>
              Select a receivable purchase order.
            </p>
          )}
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Recent GRNs</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>GRN</th>
                <th>PO</th>
                <th>Supplier</th>
                <th>Warehouse</th>
                <th>Date</th>
                <th>Items</th>
              </tr>
            </thead>
            <tbody>
              {grns.map((grn) => (
                <tr key={grn.id}>
                  <td>{grn.grn_number || grn.id}</td>
                  <td>{grn.purchase_order_number || grn.po_number || '-'}</td>
                  <td>{grn.supplier_name || '-'}</td>
                  <td>{grn.warehouse_name || '-'}</td>
                  <td>{grn.received_at || grn.created_at || '-'}</td>
                  <td>{Array.isArray(grn.items) ? grn.items.length : '-'}</td>
                </tr>
              ))}

              {grns.length === 0 ? (
                <tr>
                  <td colSpan="6">No GRNs found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}