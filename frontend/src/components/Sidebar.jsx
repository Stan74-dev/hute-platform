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
        <NavLink to="/">Dashboard</NavLink>
        <NavLink to="/pos">POS Checkout</NavLink>
        <NavLink to="/sales">Sales History</NavLink>
        <NavLink to="/refunds">Refunds</NavLink>
        {canManage ? <NavLink to="/products">Products</NavLink> : null}
        {canManage ? <NavLink to="/warehouses">Warehouses</NavLink> : null}
        {canManage ? <NavLink to="/transfers">Stock Transfers</NavLink> : null}
      </nav>
    </aside>
  )
}