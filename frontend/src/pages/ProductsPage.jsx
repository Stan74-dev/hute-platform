import { useEffect, useMemo, useState } from 'react'
import API from '../api/client'

const emptyForm = {
  sku: '',
  barcode: '',
  name: '',
  description: '',
  selling_price: '',
  cost_price: '',
  is_active: true,
}

export default function ProductsPage() {
  const [products, setProducts] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [canManage, setCanManage] = useState(false)
  const [showLowOnly, setShowLowOnly] = useState(false)

  const filteredProducts = useMemo(() => {
    const sorted = [...products].sort((a, b) => a.name.localeCompare(b.name))
    if (!showLowOnly) {
      return sorted
    }
    return sorted.filter((product) => product.low_stock)
  }, [products, showLowOnly])

  const loadProducts = async () => {
    const { data } = await API.get('/inventory/products/')
    setProducts(data)
  }

  useEffect(() => {
    loadProducts().catch((err) => console.error(err))
    API.get('/accounts/me/')
      .then((res) => setCanManage(['admin', 'manager'].includes(res.data.role)))
      .catch((err) => console.error(err))
  }, [])

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const resetForm = () => {
    setForm(emptyForm)
    setEditingId(null)
    setError('')
    setSuccess('')
  }

  const handleEdit = (product) => {
    setEditingId(product.id)
    setForm({
      sku: product.sku,
      barcode: product.barcode || '',
      name: product.name,
      description: product.description || '',
      selling_price: product.selling_price,
      cost_price: product.cost_price,
      is_active: product.is_active,
    })
    setError('')
    setSuccess('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    try {
      if (editingId) {
        await API.put(`/inventory/products/${editingId}/`, form)
        setSuccess('Product updated successfully.')
      } else {
        await API.post('/inventory/products/', form)
        setSuccess('Product created successfully.')
      }

      await loadProducts()
      resetForm()
    } catch (err) {
      const data = err.response?.data
      if (typeof data === 'string') {
        setError(data)
      } else if (data?.detail) {
        setError(data.detail)
      } else if (data) {
        setError(JSON.stringify(data))
      } else {
        setError('Could not save product.')
      }
    }
  }

  const handleDelete = async (productId) => {
    const confirmed = window.confirm('Delete this product?')
    if (!confirmed) {
      return
    }

    setError('')
    setSuccess('')

    try {
      await API.delete(`/inventory/products/${productId}/`)
      setSuccess('Product deleted successfully.')
      await loadProducts()
      if (editingId === productId) {
        resetForm()
      }
    } catch (err) {
      const data = err.response?.data
      if (typeof data === 'string') {
        setError(data)
      } else if (data?.detail) {
        setError(data.detail)
      } else if (data) {
        setError(JSON.stringify(data))
      } else {
        setError('Could not delete product.')
      }
    }
  }

  return (
    <div>
      <div className="section-header section-header-row">
        <div>
          <h2>Products</h2>
          <p className="muted-text">Manage products, pricing, barcode setup, and stock alert visibility.</p>
        </div>

        <label className="checkbox-inline">
          <input
            type="checkbox"
            checked={showLowOnly}
            onChange={(e) => setShowLowOnly(e.target.checked)}
          />
          Show low-stock only
        </label>
      </div>

      {canManage && (
        <form className="content-card form-card" onSubmit={handleSubmit}>
          <h3>{editingId ? 'Edit Product' : 'Add Product'}</h3>

          <div className="form-grid">
            <label>
              SKU
              <input name="sku" value={form.sku} onChange={handleChange} required />
            </label>

            <label>
              Barcode
              <input name="barcode" value={form.barcode} onChange={handleChange} />
            </label>

            <label className="form-span-2">
              Name
              <input name="name" value={form.name} onChange={handleChange} required />
            </label>

            <label className="form-span-2">
              Description
              <input name="description" value={form.description} onChange={handleChange} />
            </label>

            <label>
              Selling Price
              <input
                name="selling_price"
                type="number"
                step="0.01"
                value={form.selling_price}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              Cost Price
              <input
                name="cost_price"
                type="number"
                step="0.01"
                value={form.cost_price}
                onChange={handleChange}
                required
              />
            </label>

            <label className="checkbox-row">
              <input
                name="is_active"
                type="checkbox"
                checked={form.is_active}
                onChange={handleChange}
              />
              Active
            </label>
          </div>

          <div className="form-actions">
            <button className="btn btn-primary" type="submit">
              {editingId ? 'Update Product' : 'Create Product'}
            </button>
            <button className="btn btn-secondary" type="button" onClick={resetForm}>
              Clear
            </button>
          </div>

          {success ? <p className="success-text">{success}</p> : null}
          {error ? <p className="error-text">{error}</p> : null}
        </form>
      )}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>SKU</th>
              <th>Barcode</th>
              <th>Name</th>
              <th>Selling Price</th>
              <th>Cost Price</th>
              <th>Unit Profit</th>
              <th>Total Stock</th>
              <th>Alert</th>
              <th>Status</th>
              {canManage ? <th>Actions</th> : null}
            </tr>
          </thead>
          <tbody>
            {filteredProducts.map((product) => (
              <tr key={product.id} className={product.low_stock ? 'row-alert' : ''}>
                <td>{product.sku}</td>
                <td>{product.barcode || '—'}</td>
                <td>{product.name}</td>
                <td>£{Number(product.selling_price).toFixed(2)}</td>
                <td>£{Number(product.cost_price).toFixed(2)}</td>
                <td>£{Number(product.unit_profit).toFixed(2)}</td>
                <td>{product.total_stock}</td>
                <td>
                  {product.low_stock ? (
                    <span className="badge badge-danger">Low Stock</span>
                  ) : (
                    <span className="badge badge-success">OK</span>
                  )}
                </td>
                <td>{product.is_active ? 'Active' : 'Inactive'}</td>
                {canManage ? (
                  <td>
                    <div className="table-actions">
                      <button
                        type="button"
                        className="btn btn-sm btn-secondary"
                        onClick={() => handleEdit(product)}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDelete(product.id)}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}