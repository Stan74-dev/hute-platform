import { useEffect, useMemo, useState } from 'react'
import API from '../api/client'

function numberValue(value) {
  const n = Number(value || 0)
  return Number.isNaN(n) ? 0 : n
}

export default function WarehousesPage() {
  const [warehouses, setWarehouses] = useState([])
  const [stockRows, setStockRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadData = async () => {
    try {
      setLoading(true)
      setError('')

      const [warehousesRes, stockRes] = await Promise.all([
        API.get('/inventory/warehouses/'),
        API.get('/inventory/stock/'),
      ])

      setWarehouses(Array.isArray(warehousesRes.data) ? warehousesRes.data : [])
      setStockRows(Array.isArray(stockRes.data) ? stockRes.data : [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load warehouses.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const warehouseSummary = useMemo(() => {
    return warehouses.map((warehouse) => {
      const rows = stockRows.filter(
        (row) => String(row.warehouse_id) === String(warehouse.id)
      )

      const totalQuantity = rows.reduce((sum, row) => sum + numberValue(row.quantity), 0)
      const uniqueProducts = new Set(rows.map((row) => row.product_id)).size

      return {
        ...warehouse,
        totalQuantity,
        uniqueProducts,
        stockRows: rows,
      }
    })
  }, [warehouses, stockRows])

  return (
    <div>
      <div className="section-header">
        <h2>Warehouses</h2>
        <p className="muted-text">
          Review warehouse locations and stock holdings.
        </p>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading warehouses...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}

      <div className="content-card" style={{ marginTop: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', flexWrap: 'wrap' }}>
          <h3>Warehouse Stock Overview</h3>
          <button type="button" className="btn btn-secondary" onClick={loadData}>
            Reload
          </button>
        </div>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Code</th>
                <th>Location</th>
                <th>Status</th>
                <th>Products</th>
                <th>Total Stock Qty</th>
              </tr>
            </thead>
            <tbody>
              {warehouseSummary.map((warehouse) => (
                <tr key={warehouse.id}>
                  <td>{warehouse.name}</td>
                  <td>{warehouse.code}</td>
                  <td>{warehouse.location || '-'}</td>
                  <td>{warehouse.is_active ? 'Active' : 'Inactive'}</td>
                  <td>{warehouse.uniqueProducts}</td>
                  <td>{warehouse.totalQuantity}</td>
                </tr>
              ))}
              {warehouseSummary.length === 0 ? (
                <tr>
                  <td colSpan="6">No warehouses found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Stock by Warehouse</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Warehouse</th>
                <th>Product</th>
                <th>SKU</th>
                <th>Quantity</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {stockRows.map((row) => (
                <tr key={row.id}>
                  <td>{row.warehouse_name || '-'}</td>
                  <td>{row.product_name || '-'}</td>
                  <td>{row.product_sku || '-'}</td>
                  <td>{row.quantity}</td>
                  <td>{row.updated_at || '-'}</td>
                </tr>
              ))}
              {stockRows.length === 0 ? (
                <tr>
                  <td colSpan="5">No stock records found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}