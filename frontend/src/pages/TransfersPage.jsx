import { useEffect, useMemo, useState } from 'react'
import API from '../api/client'

function numberValue(value) {
  const n = Number(value || 0)
  return Number.isNaN(n) ? 0 : n
}

export default function TransfersPage() {
  const [products, setProducts] = useState([])
  const [warehouses, setWarehouses] = useState([])
  const [transfers, setTransfers] = useState([])

  const [product, setProduct] = useState('')
  const [fromWarehouse, setFromWarehouse] = useState('')
  const [toWarehouse, setToWarehouse] = useState('')
  const [quantity, setQuantity] = useState(1)

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadData = async () => {
    try {
      setLoading(true)
      setError('')

      const [productsRes, warehousesRes, transfersRes] = await Promise.all([
        API.get('/inventory/products/'),
        API.get('/inventory/warehouses/'),
        API.get('/inventory/transfers/'),
      ])

      setProducts(Array.isArray(productsRes.data) ? productsRes.data : [])
      setWarehouses(Array.isArray(warehousesRes.data) ? warehousesRes.data : [])
      setTransfers(Array.isArray(transfersRes.data) ? transfersRes.data : [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load transfer data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleCreateTransfer = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!product) {
      setError('Select a product.')
      return
    }

    if (!fromWarehouse) {
      setError('Select a source warehouse.')
      return
    }

    if (!toWarehouse) {
      setError('Select a destination warehouse.')
      return
    }

    if (String(fromWarehouse) === String(toWarehouse)) {
      setError('Source and destination warehouses cannot be the same.')
      return
    }

    if (numberValue(quantity) <= 0) {
      setError('Quantity must be greater than zero.')
      return
    }

    try {
      setSubmitting(true)

      const { data } = await API.post('/inventory/transfers/', {
        product: Number(product),
        from_warehouse: Number(fromWarehouse),
        to_warehouse: Number(toWarehouse),
        quantity: Number(quantity),
      })

      setSuccess(data?.detail || 'Stock transferred successfully.')
      setProduct('')
      setFromWarehouse('')
      setToWarehouse('')
      setQuantity(1)

      await loadData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create stock transfer.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="section-header">
        <h2>Stock Transfer</h2>
        <p className="muted-text">
          Move stock between warehouses and review transfer audit history.
        </p>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading stock transfers...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}
      {success ? <p style={{ marginTop: '16px', color: 'green' }}>{success}</p> : null}

      <div className="card-grid" style={{ marginTop: '20px' }}>
        <div className="content-card">
          <h3>Create Transfer</h3>

          <form onSubmit={handleCreateTransfer}>
            <label style={{ marginTop: '12px', display: 'block' }}>Product</label>
            <select value={product} onChange={(e) => setProduct(e.target.value)}>
              <option value="">Select product</option>
              {products.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} ({item.sku})
                </option>
              ))}
            </select>

            <label style={{ marginTop: '12px', display: 'block' }}>From Warehouse</label>
            <select value={fromWarehouse} onChange={(e) => setFromWarehouse(e.target.value)}>
              <option value="">Select source warehouse</option>
              {warehouses.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>

            <label style={{ marginTop: '12px', display: 'block' }}>To Warehouse</label>
            <select value={toWarehouse} onChange={(e) => setToWarehouse(e.target.value)}>
              <option value="">Select destination warehouse</option>
              {warehouses.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>

            <label style={{ marginTop: '12px', display: 'block' }}>Quantity</label>
            <input
              type="number"
              min="1"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
            />

            <div style={{ display: 'flex', gap: '10px', marginTop: '16px', flexWrap: 'wrap' }}>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? 'Submitting...' : 'Transfer Stock'}
              </button>

              <button
                type="button"
                className="btn btn-secondary"
                onClick={loadData}
              >
                Reload
              </button>
            </div>
          </form>
        </div>

        <div className="content-card">
          <h3>Transfer History</h3>

          <div className="table-wrap" style={{ marginTop: '12px' }}>
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Product</th>
                  <th>From</th>
                  <th>To</th>
                  <th>Qty</th>
                  <th>Created By</th>
                  <th>Created At</th>
                </tr>
              </thead>
              <tbody>
                {transfers.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>{item.product_name || '-'}</td>
                    <td>{item.from_warehouse_name || '-'}</td>
                    <td>{item.to_warehouse_name || '-'}</td>
                    <td>{item.quantity}</td>
                    <td>{item.created_by_username || '-'}</td>
                    <td>{item.created_at || '-'}</td>
                  </tr>
                ))}
                {transfers.length === 0 ? (
                  <tr>
                    <td colSpan="7">No transfers found.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}