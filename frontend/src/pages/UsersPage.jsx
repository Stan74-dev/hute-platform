import { useEffect, useState } from 'react'
import API from '../api/client'

const ROLE_OPTIONS = [
  { value: 'admin', label: 'Admin' },
  { value: 'cashier', label: 'Cashier' },
  { value: 'warehouse_staff', label: 'Warehouse Staff' },
  { value: 'finance_user', label: 'Finance User' },
]

export default function UsersPage() {
  const [users, setUsers] = useState([])
  const [query, setQuery] = useState('')

  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    email: '',
    first_name: '',
    last_name: '',
    role: 'cashier',
  })

  const [loading, setLoading] = useState(true)
  const [savingId, setSavingId] = useState(null)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadUsers = async (searchValue = '') => {
    try {
      setLoading(true)
      setError('')
      setSuccess('')

      const url = searchValue
        ? `/accounts/users/?q=${encodeURIComponent(searchValue)}`
        : '/accounts/users/'

      const { data } = await API.get(url)
      setUsers(Array.isArray(data) ? data : [])
    } catch (err) {
      const data = err.response?.data
      if (typeof data === 'string') {
        setError(data)
      } else if (data?.detail) {
        setError(data.detail)
      } else {
        setError('Could not load users.')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUsers()
  }, [])

  const updateRole = async (userId, role) => {
    try {
      setSavingId(userId)
      setError('')
      setSuccess('')

      await API.post(`/accounts/users/${userId}/role/`, { role })
      setSuccess('User role updated.')
      await loadUsers(query)
    } catch (err) {
      const data = err.response?.data
      if (typeof data === 'string') {
        setError(data)
      } else if (data?.detail) {
        setError(data.detail)
      } else {
        setError('Could not update role.')
      }
    } finally {
      setSavingId(null)
    }
  }

  const createUser = async (e) => {
    e.preventDefault()

    try {
      setCreating(true)
      setError('')
      setSuccess('')

      await API.post('/accounts/users/create/', newUser)

      setSuccess('User created successfully.')
      setNewUser({
        username: '',
        password: '',
        email: '',
        first_name: '',
        last_name: '',
        role: 'cashier',
      })

      await loadUsers(query)
    } catch (err) {
      const data = err.response?.data
      if (typeof data === 'string') {
        setError(data)
      } else if (data?.detail) {
        setError(data.detail)
      } else {
        setError('Could not create user.')
      }
    } finally {
      setCreating(false)
    }
  }

  return (
    <div>
      <div className="section-header">
        <h2>User Role Management</h2>
        <p className="muted-text">
          Create users and assign roles for admin, cashier, warehouse, and finance access.
        </p>
      </div>

      <div className="card-grid" style={{ marginTop: '18px' }}>
        <div className="content-card">
          <h3>Create User</h3>

          <form onSubmit={createUser} style={{ marginTop: '12px' }}>
            <label>Username</label>
            <input
              value={newUser.username}
              onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
              required
            />

            <label style={{ marginTop: '12px', display: 'block' }}>Password</label>
            <input
              type="password"
              value={newUser.password}
              onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
              required
            />

            <label style={{ marginTop: '12px', display: 'block' }}>Email</label>
            <input
              type="email"
              value={newUser.email}
              onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
            />

            <label style={{ marginTop: '12px', display: 'block' }}>First Name</label>
            <input
              value={newUser.first_name}
              onChange={(e) => setNewUser({ ...newUser, first_name: e.target.value })}
            />

            <label style={{ marginTop: '12px', display: 'block' }}>Last Name</label>
            <input
              value={newUser.last_name}
              onChange={(e) => setNewUser({ ...newUser, last_name: e.target.value })}
            />

            <label style={{ marginTop: '12px', display: 'block' }}>Role</label>
            <select
              value={newUser.role}
              onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
              required
            >
              {ROLE_OPTIONS.map((role) => (
                <option key={role.value} value={role.value}>
                  {role.label}
                </option>
              ))}
            </select>

            <div style={{ marginTop: '16px' }}>
              <button type="submit" className="btn btn-primary" disabled={creating}>
                {creating ? 'Creating...' : 'Create User'}
              </button>
            </div>
          </form>
        </div>

        <div className="content-card">
          <h3>Search Users</h3>

          <label>Search</label>
          <div style={{ display: 'flex', gap: '10px', marginTop: '10px', flexWrap: 'wrap' }}>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by username or email"
            />
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => loadUsers(query)}
            >
              Search
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setQuery('')
                loadUsers('')
              }}
            >
              Reset
            </button>
          </div>
        </div>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading users...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}
      {success ? <p style={{ color: 'green', marginTop: '16px' }}>{success}</p> : null}

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Users</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Name</th>
                <th>Current Role</th>
                <th>System Admin</th>
                <th>Active</th>
                <th>Change Role</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>{user.username}</td>
                  <td>{user.email || '-'}</td>
                  <td>
                    {[user.first_name, user.last_name].filter(Boolean).join(' ') || '-'}
                  </td>
                  <td>{user.role}</td>
                  <td>{user.is_superuser ? 'Yes' : 'No'}</td>
                  <td>{user.is_active ? 'Yes' : 'No'}</td>
                  <td>
                    <select
                      value={user.role === 'unassigned' ? '' : user.role}
                      onChange={(e) => updateRole(user.id, e.target.value)}
                      disabled={savingId === user.id || user.is_superuser}
                    >
                      <option value="">Select role</option>
                      {ROLE_OPTIONS.map((role) => (
                        <option key={role.value} value={role.value}>
                          {role.label}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
              {users.length === 0 ? (
                <tr>
                  <td colSpan="7">No users found.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}