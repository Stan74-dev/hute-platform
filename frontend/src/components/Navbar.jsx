import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import API from '../api/client'

export default function Navbar() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)

  useEffect(() => {
    API.get('/accounts/me/')
      .then((res) => setUser(res.data))
      .catch(() => setUser(null))
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    navigate('/login')
  }

  return (
    <header className="navbar">
      <div>
        <h1>HUTE POS</h1>
        <p>
          Retail and warehouse management
          {user ? ` • ${user.username} (${user.role})` : ''}
        </p>
      </div>
      <button className="btn btn-danger" onClick={handleLogout}>
        Logout
      </button>
    </header>
  )
}