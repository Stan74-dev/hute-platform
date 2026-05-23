import { useEffect, useMemo, useState } from 'react'
import API from '../api/client'

function formatMoney(value) {
  return Number(value || 0).toFixed(2)
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

function numberValue(value) {
  const num = Number(value || 0)
  return Number.isNaN(num) ? 0 : num
}

function getWarehouseSalesValue(item) {
  return numberValue(
    item.sales_total ||
      item.sales_value ||
      item.total_sales ||
      item.total_amount ||
      item.revenue ||
      item.sales ||
      0
  )
}

function getWarehouseProfitValue(item) {
  return numberValue(
    item.profit_total ||
      item.total_profit ||
      item.profit ||
      0
  )
}

function downloadBlobFile(blob, filename) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

function SimpleBarChart({ title, rows, valueKey, labelKey, money = false }) {
  const maxValue = Math.max(...rows.map((row) => Number(row[valueKey] || 0)), 1)

  return (
    <div className="content-card">
      <h3>{title}</h3>
      <div style={{ marginTop: '14px', display: 'grid', gap: '12px' }}>
        {rows.length === 0 ? (
          <p className="muted-text">No data available.</p>
        ) : (
          rows.map((row, index) => {
            const rawValue = Number(row[valueKey] || 0)
            const width = `${(rawValue / maxValue) * 100}%`

            return (
              <div key={`${row[labelKey] || 'row'}-${index}`}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: '12px',
                    marginBottom: '6px',
                    fontSize: '14px',
                  }}
                >
                  <span>{row[labelKey] || '-'}</span>
                  <strong>{money ? `£${formatMoney(rawValue)}` : rawValue}</strong>
                </div>
                <div
                  style={{
                    width: '100%',
                    height: '12px',
                    background: '#e5e7eb',
                    borderRadius: '999px',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width,
                      height: '100%',
                      background: '#2563eb',
                      borderRadius: '999px',
                    }}
                  />
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

export default function SalesAnalyticsPage() {
  const [dashboard, setDashboard] = useState(null)
  const [warehouses, setWarehouses] = useState([])
  const [selectedWarehouse, setSelectedWarehouse] = useState('')
  const [selectedRange, setSelectedRange] = useState('today')

  const [loading, setLoading] = useState(true)
  const [exportLoading, setExportLoading] = useState('')
  const [error, setError] = useState('')

  const loadDashboard = async (rangeValue = selectedRange, warehouseValue = selectedWarehouse) => {
    try {
      setLoading(true)
      setError('')

      const params = new URLSearchParams()
      if (rangeValue) params.set('range', rangeValue)
      if (warehouseValue) params.set('warehouse', warehouseValue)

      const [dashboardRes, warehousesRes] = await Promise.all([
        API.get(`/sales/analytics/dashboard/?${params.toString()}`),
        API.get('/inventory/warehouses/'),
      ])

      setDashboard(dashboardRes.data || null)
      setWarehouses(Array.isArray(warehousesRes.data) ? warehousesRes.data : [])
    } catch (err) {
      const data = err.response?.data
      if (typeof data === 'string') {
        setError(data)
      } else if (data?.detail) {
        setError(data.detail)
      } else {
        setError('Could not load sales analytics.')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboard()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const exportCsv = async (endpoint, filename, key) => {
    try {
      setExportLoading(key)
      setError('')

      const params = new URLSearchParams()
      if (selectedRange) params.set('range', selectedRange)
      if (selectedWarehouse) params.set('warehouse', selectedWarehouse)

      const response = await API.get(`${endpoint}?${params.toString()}`, {
        responseType: 'blob',
      })

      downloadBlobFile(response.data, filename)
    } catch (_err) {
      setError('Could not export CSV.')
    } finally {
      setExportLoading('')
    }
  }

  const summary = dashboard?.summary || {
    total_sales: 0,
    total_profit: 0,
    tax_amount: 0,
    transactions: 0,
    transaction_count: 0,
    average_sale: 0,
  }

  const topProducts = Array.isArray(dashboard?.top_products) ? dashboard.top_products : []
  const warehouseBreakdown = Array.isArray(dashboard?.warehouse_breakdown)
    ? dashboard.warehouse_breakdown
    : []
  const recentSales = Array.isArray(dashboard?.recent_sales) ? dashboard.recent_sales : []

  const topProductChartData = useMemo(() => {
    return topProducts.map((item) => ({
      name: item.product_name || item.product || '-',
      qty: numberValue(item.qty_sold || item.quantity || item.units_sold || 0),
    }))
  }, [topProducts])

  const warehouseSalesChartData = useMemo(() => {
    return warehouseBreakdown.map((item) => ({
      name: item.warehouse_name || item.warehouse || '-',
      total: getWarehouseSalesValue(item),
    }))
  }, [warehouseBreakdown])

  return (
    <div>
      <div
        className="section-header"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          gap: '16px',
          alignItems: 'start',
          flexWrap: 'wrap',
        }}
      >
        <div>
          <h2>Sales Analytics</h2>
          <p className="muted-text">
            Sales performance, top products, warehouse trends, and exports.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() =>
              exportCsv('/sales/analytics/export/summary/', 'sales_summary.csv', 'summary')
            }
            disabled={exportLoading === 'summary'}
          >
            {exportLoading === 'summary' ? 'Exporting...' : 'Export Summary'}
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() =>
              exportCsv(
                '/sales/analytics/export/transactions/',
                'sales_transactions.csv',
                'transactions'
              )
            }
            disabled={exportLoading === 'transactions'}
          >
            {exportLoading === 'transactions' ? 'Exporting...' : 'Export Transactions'}
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={() =>
              exportCsv('/sales/analytics/export/top-products/', 'sales_top_products.csv', 'products')
            }
            disabled={exportLoading === 'products'}
          >
            {exportLoading === 'products' ? 'Exporting...' : 'Export Top Products'}
          </button>
        </div>
      </div>

      <div className="card-grid" style={{ marginTop: '18px' }}>
        <div className="content-card">
          <label>Range</label>
          <select
            value={selectedRange}
            onChange={(e) => {
              const value = e.target.value
              setSelectedRange(value)
              loadDashboard(value, selectedWarehouse)
            }}
          >
            <option value="today">Today</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="month">This Month</option>
          </select>
        </div>

        <div className="content-card">
          <label>Warehouse</label>
          <select
            value={selectedWarehouse}
            onChange={(e) => {
              const value = e.target.value
              setSelectedWarehouse(value)
              loadDashboard(selectedRange, value)
            }}
          >
            <option value="">All Warehouses</option>
            {warehouses.map((warehouse) => (
              <option key={warehouse.id} value={warehouse.id}>
                {warehouse.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading sales analytics...</p> : null}

      {error ? (
        <p className="error-text" style={{ marginTop: '16px' }}>
          {error}
        </p>
      ) : null}

      <div className="stats-grid" style={{ marginTop: '18px' }}>
        <div className="stat-card">
          <span>Total Sales</span>
          <strong>£{formatMoney(summary.total_sales || summary.total_amount)}</strong>
        </div>

        <div className="stat-card">
          <span>Total Profit</span>
          <strong>£{formatMoney(summary.total_profit)}</strong>
        </div>

        <div className="stat-card">
          <span>Sales Tax / VAT</span>
          <strong>£{formatMoney(summary.tax_amount)}</strong>
        </div>

        <div className="stat-card">
          <span>Transactions</span>
          <strong>{summary.transactions || summary.transaction_count || summary.sales_count || 0}</strong>
        </div>

        <div className="stat-card">
          <span>Average Sale</span>
          <strong>£{formatMoney(summary.average_sale)}</strong>
        </div>
      </div>

      <div className="card-grid" style={{ marginTop: '20px' }}>
        <SimpleBarChart
          title="Top Products by Quantity"
          rows={topProductChartData}
          valueKey="qty"
          labelKey="name"
        />

        <SimpleBarChart
          title="Warehouse Sales Value"
          rows={warehouseSalesChartData}
          valueKey="total"
          labelKey="name"
          money
        />
      </div>

      <div className="card-grid" style={{ marginTop: '20px' }}>
        <div className="content-card">
          <h3>Top Products</h3>

          <div className="table-wrap" style={{ marginTop: '12px' }}>
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>SKU</th>
                  <th>Qty Sold</th>
                  <th>Revenue</th>
                  <th>Profit</th>
                </tr>
              </thead>

              <tbody>
                {topProducts.map((item) => (
                  <tr key={item.product_id || item.product_sku || item.product_name}>
                    <td>{item.product_name || item.product || '-'}</td>
                    <td>{item.product_sku || item.sku || '-'}</td>
                    <td>{item.qty_sold || item.quantity || item.units_sold || 0}</td>
                    <td>£{formatMoney(item.revenue || item.total_revenue)}</td>
                    <td>£{formatMoney(item.profit)}</td>
                  </tr>
                ))}

                {topProducts.length === 0 ? (
                  <tr>
                    <td colSpan="5">No top-product data found.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>

        <div className="content-card">
          <h3>Warehouse Breakdown</h3>

          <div className="table-wrap" style={{ marginTop: '12px' }}>
            <table>
              <thead>
                <tr>
                  <th>Warehouse</th>
                  <th>Sales</th>
                  <th>Profit</th>
                  <th>Transactions</th>
                </tr>
              </thead>

              <tbody>
                {warehouseBreakdown.map((item) => (
                  <tr key={item.warehouse_id || item.warehouse_name || item.warehouse}>
                    <td>{item.warehouse_name || item.warehouse || '-'}</td>
                    <td>£{formatMoney(getWarehouseSalesValue(item))}</td>
                    <td>£{formatMoney(getWarehouseProfitValue(item))}</td>
                    <td>{item.transactions || item.sales_count || 0}</td>
                  </tr>
                ))}

                {warehouseBreakdown.length === 0 ? (
                  <tr>
                    <td colSpan="4">No warehouse breakdown found.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Recent Transactions</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Receipt</th>
                <th>Date</th>
                <th>Warehouse</th>
                <th>Cashier</th>
                <th>Payment</th>
                <th>Total</th>
                <th>Sales Tax / VAT</th>
                <th>Profit</th>
              </tr>
            </thead>

            <tbody>
              {recentSales.map((sale) => (
                <tr key={sale.id}>
                  <td>{sale.receipt_number}</td>
                  <td>{formatDate(sale.created_at)}</td>
                  <td>{sale.warehouse_name}</td>
                  <td>{sale.cashier_username || '-'}</td>
                  <td>{sale.payment_method}</td>
                  <td>£{formatMoney(sale.total_amount)}</td>
                  <td>£{formatMoney(sale.tax_amount || sale.tax)}</td>
                  <td>£{formatMoney(sale.total_profit)}</td>
                </tr>
              ))}

              {recentSales.length === 0 ? (
                <tr>
                  <td colSpan="8">No recent transactions found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}