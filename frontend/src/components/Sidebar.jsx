import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import API from '../api/client'

export default function Sidebar() {
  const [role, setRole] = useState('cashier')

  useEffect(() => {
    API.get('/accounts/me/')
      .then((res) => setRole(res.data.role || 'cashier'))
      .catch(() => setRole('cashier'))
  }, [])

  const canManage = ['admin', 'manager'].includes(role)

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">HUTE</div>
      <nav className="sidebar-nav">
        <div className="nav-section">
          <div className="nav-section-title">Operations</div>
          <NavLink to="/">Dashboard</NavLink>
          <NavLink to="/pos">POS Checkout</NavLink>
        </div>

        <div className="nav-section">
          <div className="nav-section-title">Sales</div>
          <NavLink to="/sales">Sales History</NavLink>
          <NavLink to="/refunds">Refunds</NavLink>
        </div>

        {canManage ? (
          <div className="nav-section">
            <div className="nav-section-title">Inventory & Procurement</div>
            <NavLink to="/products">Products</NavLink>
            <NavLink to="/warehouses">Warehouses</NavLink>
            <NavLink to="/transfers">Stock Transfers</NavLink>
          </div>
        ) : null}
      </nav>
    </aside>
  )
}