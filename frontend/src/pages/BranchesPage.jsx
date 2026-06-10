import { useEffect, useState } from 'react'
import API from '../api/client'

export default function BranchesPage() {
  const [branches, setBranches] = useState([])
  const [form, setForm] = useState({ name: '', code: '', address: '', phone: '', manager_name: '' })
  const [error, setError] = useState('')

  const loadBranches = async () => {
    try {
      const res = await API.get('/branches/branches/')
      setBranches(res.data.results || res.data || [])
    } catch {
      setError('Could not load branches.')
    }
  }

  useEffect(() => { loadBranches() }, [])

  const saveBranch = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await API.post('/branches/branches/', form)
      setForm({ name: '', code: '', address: '', phone: '', manager_name: '' })
      loadBranches()
    } catch {
      setError('Could not save branch.')
    }
  }

  return (
    <div>
      <h2>Branches</h2>
      {error ? <div className="alert alert-error">{error}</div> : null}
      <div className="content-card">
        <h3>Add Branch</h3>
        <form onSubmit={saveBranch} className="form-grid">
          <input placeholder="Branch name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <input placeholder="Code" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} required />
          <input placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <input placeholder="Manager" value={form.manager_name} onChange={(e) => setForm({ ...form, manager_name: e.target.value })} />
          <textarea placeholder="Address" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          <button className="btn btn-primary" type="submit">Save Branch</button>
        </form>
      </div>
      <div className="content-card" style={{ marginTop: 16 }}>
        <h3>Branch List</h3>
        <table>
          <thead><tr><th>Name</th><th>Code</th><th>Manager</th><th>Phone</th><th>Status</th></tr></thead>
          <tbody>
            {branches.map((b) => <tr key={b.id}><td>{b.name}</td><td>{b.code}</td><td>{b.manager_name || '-'}</td><td>{b.phone || '-'}</td><td>{b.is_active ? 'Active' : 'Inactive'}</td></tr>)}
            {branches.length === 0 ? <tr><td colSpan="5">No branches yet.</td></tr> : null}
          </tbody>
        </table>
      </div>
    </div>
  )
}
