import { useState } from 'react'
import API from '../api/client'

export default function PaymentSettingsPage() {
  const [form, setForm] = useState({ provider: 'ecocash', amount: '1.00', currency: 'USD', customer_phone: '' })
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const initiate = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)
    try {
      const res = await API.post('/payments/initiate/', form)
      setResult(res.data)
    } catch {
      setError('Could not initiate payment.')
    }
  }

  return (
    <div>
      <h2>Payment Integrations</h2>
      {error ? <div className="alert alert-error">{error}</div> : null}
      <div className="content-card">
        <form onSubmit={initiate} className="form-grid">
          <select value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })}>
            <option value="ecocash">EcoCash</option>
            <option value="innbucks">InnBucks</option>
            <option value="mukuru">Mukuru</option>
            <option value="zipit">ZIPIT</option>
            <option value="cash">Cash</option>
            <option value="card">Card</option>
          </select>
          <input value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="Amount" />
          <input value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} placeholder="Currency" />
          <input value={form.customer_phone} onChange={(e) => setForm({ ...form, customer_phone: e.target.value })} placeholder="Customer phone" />
          <button className="btn btn-primary" type="submit">Create Payment Request</button>
        </form>
      </div>
      {result ? <pre>{JSON.stringify(result, null, 2)}</pre> : null}
    </div>
  )
}
