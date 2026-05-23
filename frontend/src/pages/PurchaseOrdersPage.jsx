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

function canReceive(po) {
  const status = String(po?.status || '').toLowerCase()
  return ['submitted', 'partial'].includes(status) && numberValue(po?.pending_quantity_total) > 0
}

function statusLabel(po) {
  const pending = numberValue(po?.pending_quantity_total)
  const received = numberValue(po?.received_quantity_total)

  if (pending <= 0 && received > 0) return 'Fully Received'
  if (received > 0 && pending > 0) return 'Partially Received'
  return String(po?.status || 'submitted')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export default function PurchaseOrdersPage() {
  const [purchaseOrders, setPurchaseOrders] = useState([])
  const [selectedPoId, setSelectedPoId] = useState('')
  const [selectedPO, setSelectedPO] = useState(null)

  const [suppliers, setSuppliers] = useState([])
  const [warehouses, setWarehouses] = useState([])
  const [products, setProducts] = useState([])

  const [supplierId, setSupplierId] = useState('')
  const [warehouseId, setWarehouseId] = useState('')
  const [notes, setNotes] = useState('')
  const [items, setItems] = useState([{ product_id: '', quantity: 1, unit_cost: 0 }])
  const [receiving, setReceiving] = useState({})

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [receivingSubmitting, setReceivingSubmitting] = useState(false)
  const [invoiceSubmitting, setInvoiceSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadLists = async () => {
    const [poRes, supplierRes, warehouseRes, productRes] = await Promise.all([
      API.get('/inventory/purchase-orders/'),
      API.get('/inventory/suppliers/'),
      API.get('/inventory/warehouses/'),
      API.get('/inventory/products/'),
    ])

    const poRows = Array.isArray(poRes.data) ? poRes.data : []
    setPurchaseOrders(poRows)
    setSuppliers(Array.isArray(supplierRes.data) ? supplierRes.data : [])
    setWarehouses(Array.isArray(warehouseRes.data) ? warehouseRes.data : [])
    setProducts(Array.isArray(productRes.data) ? productRes.data : [])

    if (poRows.length > 0) {
      const stillExists = poRows.find((po) => String(po.id) === String(selectedPoId))
      if (!stillExists) {
        setSelectedPoId(String(poRows[0].id))
      }
    } else {
      setSelectedPoId('')
    }

    return poRows
  }

  const loadSelectedPO = async (poId) => {
    if (!poId) {
      setSelectedPO(null)
      setReceiving({})
      return null
    }

    const { data } = await API.get(`/inventory/purchase-orders/${poId}/`)
    setSelectedPO(data || null)

    const initialReceiving = {}
    ;(data?.items || []).forEach((item) => {
      initialReceiving[item.id] = {
        quantity_received: 0,
        batch_number: '',
        expiry_date: '',
      }
    })
    setReceiving(initialReceiving)

    return data
  }

  const loadData = async (keepSelected = true) => {
    try {
      setLoading(true)
      setError('')
      setSuccess('')

      const poRows = await loadLists()

      if (keepSelected && selectedPoId) {
        await loadSelectedPO(selectedPoId)
      } else if (poRows.length > 0) {
        await loadSelectedPO(poRows[0].id)
      } else {
        setSelectedPO(null)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load purchase order data.')
      setPurchaseOrders([])
      setSelectedPO(null)
      setSuppliers([])
      setWarehouses([])
      setProducts([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData(false)
  }, [])

  const handleSelectPO = async (poId) => {
    try {
      setError('')
      setSuccess('')
      setSelectedPoId(String(poId))
      await loadSelectedPO(poId)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load selected purchase order.')
    }
  }

  const addItemRow = () => {
    setItems((prev) => [...prev, { product_id: '', quantity: 1, unit_cost: 0 }])
  }

  const removeItemRow = (index) => {
    setItems((prev) => prev.filter((_, i) => i !== index))
  }

  const updateItemRow = (index, field, value) => {
    setItems((prev) =>
      prev.map((item, i) =>
        i === index
          ? { ...item, [field]: value }
          : item
      )
    )
  }

  const handleReceiveQtyChange = (id, value, maxAllowed) => {
    const qty = Math.max(0, numberValue(value))
    const capped = Math.min(qty, numberValue(maxAllowed))

    setReceiving((prev) => ({
      ...prev,
      [id]: {
        ...(prev[id] || {}),
        quantity_received: capped,
      },
    }))
  }

  const handleReceiveBatchChange = (id, value) => {
    setReceiving((prev) => ({
      ...prev,
      [id]: {
        ...(prev[id] || {}),
        batch_number: value,
      },
    }))
  }

  const handleReceiveExpiryChange = (id, value) => {
    setReceiving((prev) => ({
      ...prev,
      [id]: {
        ...(prev[id] || {}),
        expiry_date: value,
      },
    }))
  }

  const createPurchaseOrder = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!supplierId) {
      setError('Please select a supplier.')
      return
    }

    if (!warehouseId) {
      setError('Please select a warehouse.')
      return
    }

    const cleanItems = items
      .map((item) => ({
        product: Number(item.product_id),
        quantity: Number(item.quantity),
        unit_cost: Number(item.unit_cost),
      }))
      .filter((item) => item.product && item.quantity > 0)

    if (!cleanItems.length) {
      setError('Add at least one purchase order item.')
      return
    }

    try {
      setSubmitting(true)

      const { data } = await API.post('/inventory/purchase-orders/', {
        supplier: Number(supplierId),
        warehouse: Number(warehouseId),
        notes,
        items: cleanItems,
      })

      setSuccess(data?.detail || 'Purchase order created successfully.')
      setSupplierId('')
      setWarehouseId('')
      setNotes('')
      setItems([{ product_id: '', quantity: 1, unit_cost: 0 }])

      await loadData(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create purchase order.')
    } finally {
      setSubmitting(false)
    }
  }

  const receivingItems = useMemo(() => {
    if (!selectedPO?.items) return []

    return selectedPO.items.map((item) => {
      const current = receiving[item.id] || {
        quantity_received: 0,
        batch_number: '',
        expiry_date: '',
      }

      return {
        ...item,
        quantity_received: numberValue(current.quantity_received),
        batch_number: current.batch_number || '',
        expiry_date: current.expiry_date || '',
      }
    })
  }, [selectedPO, receiving])

  const hasReceivableQty = useMemo(() => {
    return receivingItems.some((item) => item.quantity_received > 0)
  }, [receivingItems])

  const submitReceiving = async () => {
    setError('')
    setSuccess('')

    if (!selectedPO) {
      setError('Select a purchase order first.')
      return
    }

    if (!canReceive(selectedPO)) {
      setError('This purchase order is closed for receiving.')
      return
    }

    const rowsWithQty = receivingItems.filter((item) => item.quantity_received > 0)

    if (!rowsWithQty.length) {
      setError('Enter at least one quantity to receive.')
      return
    }

    const rowMissingBatch = rowsWithQty.find((item) => !String(item.batch_number || '').trim())
    if (rowMissingBatch) {
      setError(`Batch number is required for ${rowMissingBatch.product_name}.`)
      return
    }

    const payload = {
      purchase_order: Number(selectedPO.id),
      notes: '',
      items: rowsWithQty.map((item) => ({
        purchase_order_item: item.id,
        quantity_received: item.quantity_received,
        batch_number: item.batch_number,
        expiry_date: item.expiry_date || null,
      })),
    }

    try {
      setReceivingSubmitting(true)

      const { data } = await API.post('/inventory/grns/', payload)

      const freshPO = await loadSelectedPO(selectedPO.id)
      await loadLists()

      setSuccess(
        `${data?.detail || 'Goods received successfully.'} Current status: ${statusLabel(freshPO || selectedPO)}.`
      )
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        err.response?.data?.error ||
        'Could not complete receiving.'
      )
    } finally {
      setReceivingSubmitting(false)
    }
  }

  const generateInvoice = async () => {
    setError('')
    setSuccess('')

    if (!selectedPO) {
      setError('Select a purchase order first.')
      return
    }

    try {
      setInvoiceSubmitting(true)
      const { data } = await API.post(`/inventory/purchase-orders/${selectedPO.id}/generate-invoice/`)
      setSuccess(data?.detail || 'Supplier invoice generated successfully.')
      await loadSelectedPO(selectedPO.id)
      await loadLists()
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        err.response?.data?.error ||
        'Could not generate supplier invoice.'
      )
    } finally {
      setInvoiceSubmitting(false)
    }
  }

  const totalDraftAmount = useMemo(() => {
    return items.reduce((sum, item) => {
      return sum + (numberValue(item.quantity) * numberValue(item.unit_cost))
    }, 0)
  }, [items])

  return (
    <div>
      <div className="section-header">
        <h2>Purchase Orders</h2>
        <p className="muted-text">
          Create POs, receive goods with batch and expiry tracking, review GRN history, and generate supplier invoices.
        </p>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading purchase orders...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}
      {success ? <p style={{ marginTop: '16px', color: 'green' }}>{success}</p> : null}

      <div className="stats-grid" style={{ marginTop: '18px' }}>
        <div className="stat-card"><span>Suppliers</span><strong>{suppliers.length}</strong></div>
        <div className="stat-card"><span>Warehouses</span><strong>{warehouses.length}</strong></div>
        <div className="stat-card"><span>Products</span><strong>{products.length}</strong></div>
        <div className="stat-card"><span>POs</span><strong>{purchaseOrders.length}</strong></div>
      </div>

      <div className="card-grid" style={{ marginTop: '20px' }}>
        <div className="content-card">
          <h3>Create Purchase Order</h3>

          <form onSubmit={createPurchaseOrder}>
            <label style={{ marginTop: '12px', display: 'block' }}>Supplier</label>
            <select value={supplierId} onChange={(e) => setSupplierId(e.target.value)}>
              <option value="">Select supplier</option>
              {suppliers.map((supplier) => (
                <option key={supplier.id} value={supplier.id}>
                  {supplier.name}
                </option>
              ))}
            </select>

            <label style={{ marginTop: '12px', display: 'block' }}>Warehouse</label>
            <select value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)}>
              <option value="">Select warehouse</option>
              {warehouses.map((warehouse) => (
                <option key={warehouse.id} value={warehouse.id}>
                  {warehouse.name}
                </option>
              ))}
            </select>

            <label style={{ marginTop: '12px', display: 'block' }}>Notes</label>
            <textarea
              rows="3"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional notes"
            />

            <div style={{ marginTop: '18px' }}>
              <h4>Items</h4>

              <div className="table-wrap" style={{ marginTop: '10px' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Quantity</th>
                      <th>Unit Cost</th>
                      <th>Line Total</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item, index) => (
                      <tr key={index}>
                        <td>
                          <select
                            value={item.product_id}
                            onChange={(e) => updateItemRow(index, 'product_id', e.target.value)}
                          >
                            <option value="">Select product</option>
                            {products.map((product) => (
                              <option key={product.id} value={product.id}>
                                {product.name} ({product.sku})
                              </option>
                            ))}
                          </select>
                        </td>
                        <td>
                          <input
                            type="number"
                            min="1"
                            value={item.quantity}
                            onChange={(e) => updateItemRow(index, 'quantity', e.target.value)}
                            style={{ width: '90px' }}
                          />
                        </td>
                        <td>
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={item.unit_cost}
                            onChange={(e) => updateItemRow(index, 'unit_cost', e.target.value)}
                            style={{ width: '110px' }}
                          />
                        </td>
                        <td>£{money(numberValue(item.quantity) * numberValue(item.unit_cost))}</td>
                        <td>
                          <button
                            type="button"
                            className="btn btn-danger"
                            onClick={() => removeItemRow(index)}
                            disabled={items.length === 1}
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '12px', flexWrap: 'wrap' }}>
                <button type="button" className="btn btn-secondary" onClick={addItemRow}>
                  Add Item
                </button>

                <div style={{ marginLeft: 'auto', fontWeight: 700 }}>
                  Draft Total: £{money(totalDraftAmount)}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: '18px', flexWrap: 'wrap' }}>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? 'Creating...' : 'Create Purchase Order'}
              </button>

              <button type="button" className="btn btn-secondary" onClick={() => loadData(true)}>
                Reload
              </button>
            </div>
          </form>
        </div>

        <div className="content-card">
          <h3>Supplier List</h3>

          <div className="table-wrap" style={{ marginTop: '12px' }}>
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Contact</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {suppliers.map((supplier) => (
                  <tr key={supplier.id}>
                    <td>{supplier.name}</td>
                    <td>{supplier.contact_person || '-'}</td>
                    <td>{supplier.email || '-'}</td>
                    <td>{supplier.phone || '-'}</td>
                    <td>{supplier.is_active ? 'Active' : 'Inactive'}</td>
                  </tr>
                ))}
                {suppliers.length === 0 ? (
                  <tr>
                    <td colSpan="5">No suppliers found.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <h3>Purchase Order History</h3>
            <p className="muted-text">Click a row to select a purchase order.</p>
          </div>
          <div style={{ fontWeight: 700 }}>
            Selected: {selectedPO ? selectedPO.po_number : 'None'}
          </div>
        </div>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>PO Number</th>
                <th>Supplier</th>
                <th>Warehouse</th>
                <th>Status</th>
                <th>Total</th>
                <th>Ordered</th>
                <th>Received</th>
                <th>Pending</th>
                <th>Created By</th>
                <th>Created At</th>
              </tr>
            </thead>
            <tbody>
              {purchaseOrders.map((po) => {
                const isSelected = String(po.id) === String(selectedPoId)

                return (
                  <tr
                    key={po.id}
                    onClick={() => handleSelectPO(po.id)}
                    style={{
                      cursor: 'pointer',
                      background: isSelected ? '#dbeafe' : 'transparent',
                      outline: isSelected ? '2px solid #2563eb' : 'none',
                    }}
                  >
                    <td>{po.po_number}</td>
                    <td>{po.supplier_name || '-'}</td>
                    <td>{po.warehouse_name || '-'}</td>
                    <td>{statusLabel(po)}</td>
                    <td>£{money(po.total_amount)}</td>
                    <td>{numberValue(po.ordered_quantity_total)}</td>
                    <td>{numberValue(po.received_quantity_total)}</td>
                    <td>{numberValue(po.pending_quantity_total)}</td>
                    <td>{po.created_by_username || '-'}</td>
                    <td>{po.created_at || '-'}</td>
                  </tr>
                )
              })}
              {purchaseOrders.length === 0 ? (
                <tr>
                  <td colSpan="10">No purchase orders found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      {selectedPO ? (
        <div className="content-card" style={{ marginTop: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div>
              <h3>Selected PO Details</h3>
              <p className="muted-text">
                Receiving now requires a batch number for each received line. Expiry date is optional but recommended.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={generateInvoice}
                disabled={invoiceSubmitting || Boolean(selectedPO.invoice)}
              >
                {invoiceSubmitting
                  ? 'Generating Invoice...'
                  : selectedPO.invoice
                    ? 'Invoice Already Exists'
                    : 'Generate Supplier Invoice'}
              </button>

              <button
                type="button"
                className="btn btn-primary"
                onClick={submitReceiving}
                disabled={receivingSubmitting || !canReceive(selectedPO) || !hasReceivableQty}
              >
                {receivingSubmitting
                  ? 'Receiving...'
                  : !canReceive(selectedPO)
                    ? 'Receiving Closed'
                    : !hasReceivableQty
                      ? 'Enter Quantities First'
                      : 'Receive Goods'}
              </button>
            </div>
          </div>

          <div className="table-wrap" style={{ marginTop: '12px' }}>
            <table>
              <tbody>
                <tr><th>PO Number</th><td>{selectedPO.po_number}</td></tr>
                <tr><th>Supplier</th><td>{selectedPO.supplier_name || '-'}</td></tr>
                <tr><th>Warehouse</th><td>{selectedPO.warehouse_name || '-'}</td></tr>
                <tr><th>Status</th><td>{statusLabel(selectedPO)}</td></tr>
                <tr><th>Total</th><td>£{money(selectedPO.total_amount)}</td></tr>
                <tr><th>Ordered</th><td>{numberValue(selectedPO.ordered_quantity_total)}</td></tr>
                <tr><th>Received</th><td>{numberValue(selectedPO.received_quantity_total)}</td></tr>
                <tr><th>Pending</th><td>{numberValue(selectedPO.pending_quantity_total)}</td></tr>
                <tr><th>Created By</th><td>{selectedPO.created_by_username || '-'}</td></tr>
                <tr><th>Created At</th><td>{selectedPO.created_at || '-'}</td></tr>
                <tr><th>Notes</th><td>{selectedPO.notes || '-'}</td></tr>
                <tr>
                  <th>Supplier Invoice</th>
                  <td>
                    {selectedPO.invoice
                      ? `${selectedPO.invoice.invoice_number} (${selectedPO.invoice.status})`
                      : 'Not generated'}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="table-wrap" style={{ marginTop: '16px' }}>
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>SKU</th>
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
                {(receivingItems || []).map((item) => (
                  <tr key={item.id}>
                    <td>{item.product_name || '-'}</td>
                    <td>{item.product_sku || '-'}</td>
                    <td>{numberValue(item.quantity)}</td>
                    <td>{numberValue(item.received_quantity)}</td>
                    <td>{numberValue(item.pending_quantity)}</td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        max={numberValue(item.pending_quantity)}
                        value={item.quantity_received}
                        onChange={(e) =>
                          handleReceiveQtyChange(item.id, e.target.value, item.pending_quantity)
                        }
                        style={{ width: '90px' }}
                        disabled={!canReceive(selectedPO)}
                      />
                    </td>
                    <td>
                      <input
                        type="text"
                        value={item.batch_number}
                        onChange={(e) => handleReceiveBatchChange(item.id, e.target.value)}
                        placeholder="Required if receiving"
                        style={{ width: '140px' }}
                        disabled={!canReceive(selectedPO)}
                      />
                    </td>
                    <td>
                      <input
                        type="date"
                        value={item.expiry_date}
                        onChange={(e) => handleReceiveExpiryChange(item.id, e.target.value)}
                        style={{ width: '150px' }}
                        disabled={!canReceive(selectedPO)}
                      />
                    </td>
                    <td>£{money(item.unit_cost)}</td>
                    <td>£{money(item.line_total)}</td>
                  </tr>
                ))}
                {(receivingItems || []).length === 0 ? (
                  <tr>
                    <td colSpan="10">No items found for this purchase order.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>

          <div className="content-card" style={{ marginTop: '18px', background: '#f8fafc' }}>
            <h4>GRN History</h4>

            <div className="table-wrap" style={{ marginTop: '12px' }}>
              <table>
                <thead>
                  <tr>
                    <th>GRN Number</th>
                    <th>Total Qty Received</th>
                    <th>Created By</th>
                    <th>Created At</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {(selectedPO.grns || []).map((grn) => (
                    <tr key={grn.id}>
                      <td>{grn.grn_number}</td>
                      <td>{numberValue(grn.total_received_quantity)}</td>
                      <td>{grn.created_by_username || '-'}</td>
                      <td>{grn.created_at || '-'}</td>
                      <td>{grn.notes || '-'}</td>
                    </tr>
                  ))}
                  {(selectedPO.grns || []).length === 0 ? (
                    <tr>
                      <td colSpan="5">No GRN history for this purchase order yet.</td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>

            {(selectedPO.grns || []).map((grn) => (
              <div key={`grn-items-${grn.id}`} style={{ marginTop: '16px' }}>
                <div style={{ fontWeight: 700 }}>
                  {grn.grn_number} items
                </div>

                <div className="table-wrap" style={{ marginTop: '8px' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>SKU</th>
                        <th>Batch Number</th>
                        <th>Expiry Date</th>
                        <th>Qty Received</th>
                        <th>Unit Cost</th>
                        <th>Line Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(grn.items || []).map((grnItem) => (
                        <tr key={grnItem.id}>
                          <td>{grnItem.product_name || '-'}</td>
                          <td>{grnItem.product_sku || '-'}</td>
                          <td>{grnItem.batch_number || '-'}</td>
                          <td>{grnItem.expiry_date || '-'}</td>
                          <td>{numberValue(grnItem.quantity_received)}</td>
                          <td>£{money(grnItem.unit_cost)}</td>
                          <td>£{money(grnItem.line_total)}</td>
                        </tr>
                      ))}
                      {(grn.items || []).length === 0 ? (
                        <tr>
                          <td colSpan="7">No GRN items found.</td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}