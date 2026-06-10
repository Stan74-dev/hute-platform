import { useMemo, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'

function parseStoredUser() {
  try {
    const raw = localStorage.getItem('user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function userIsAdmin(user) {
  if (!user) return true
  return Boolean(user.is_staff || user.is_superuser)
}

export default function Layout() {
  const location = useLocation()
  const user = parseStoredUser()
  const isAdmin = userIsAdmin(user)

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  const menuSections = useMemo(() => {
    const sections = [
      {
        key: 'operations',
        label: 'Operations',
        items: [
          { label: 'Dashboard', path: '/dashboard' },
          { label: 'Owner Mobile', path: '/owner-mobile' },
          { label: 'Executive Dashboard', path: '/executive-dashboard' },
          { label: 'Historical Trends', path: '/historical-trends' },
          { label: 'Day Detail', path: '/day-detail' },
        ],
      },
      {
        key: 'sales',
        label: 'Sales',
        items: [
          { label: 'POS', path: '/pos' },
          { label: 'Sales', path: '/sales' },
          { label: 'Refunds', path: '/refunds' },
          { label: 'Sales Analytics', path: '/sales-analytics' },
        ],
      },
      {
        key: 'inventory',
        label: 'Inventory & Procurement',
        items: [
          { label: 'Products', path: '/products' },
          { label: 'Warehouses', path: '/warehouses' },
          { label: 'Branches', path: '/branches' },
          { label: 'Transfers', path: '/transfers' },
          { label: 'Purchase Orders', path: '/purchase-orders' },
          { label: 'Goods Received', path: '/goods-received' },
        ],
      },
      {
        key: 'shifts',
        label: 'Shifts & Terminals',
        items: [
          { label: 'Shift', path: '/shift' },
          { label: 'All Shifts', path: '/all-shifts' },
          { label: 'Shift Variance', path: '/shift-variance' },
          { label: 'Shift Sales Report', path: '/shift-sales-report' },
          { label: 'Terminals', path: '/terminals' },
          { label: 'Terminal Activity', path: '/terminal-activity' },
        ],
      },
      {
        key: 'risk',
        label: 'Risk & Control',
        items: [
          { label: 'Anomaly Dashboard', path: '/anomaly-dashboard' },
          { label: 'Anomaly Cases', path: '/anomaly-cases' },
          { label: 'Daily Summary', path: '/daily-summary' },
          { label: 'Audit Trail', path: '/audit-trail' },
        ],
      },
      {
        key: 'enterprise',
        label: 'Enterprise',
        items: [
          { label: 'Fiscalisation', path: '/fiscalisation' },
          { label: 'Multi Currency', path: '/multi-currency' },
          { label: 'Mobile Money', path: '/mobile-money' },
          { label: 'Licensing', path: '/licensing' },
        ],
      },
    ]

    if (isAdmin) {
      sections.push({
        key: 'admin',
        label: 'Administration',
        items: [
          { label: 'Users', path: '/users' },
          { label: 'Finance', path: '/finance' },
          { label: 'Tax Summary', path: '/tax-summary' },
          { label: 'Payment Settings', path: '/payment-settings' },
        ],
      })
    }

    return sections
  }, [isAdmin])

  const buildInitialOpenState = () => {
    const state = {}

    for (const section of menuSections) {
      const hasActiveItem = section.items.some((item) => {
        return location.pathname === item.path || location.pathname.startsWith(`${item.path}/`)
      })
      state[section.key] = hasActiveItem
    }

    return state
  }

  const [openSections, setOpenSections] = useState(buildInitialOpenState)

  const toggleSection = (key) => {
    setOpenSections((prev) => ({
      ...prev,
      [key]: !prev[key],
    }))
  }

  return (
    <div className="app-shell" style={{ display: 'flex', minHeight: '100vh' }}>
      <aside
        style={{
          width: '300px',
          background: '#0f172a',
          color: '#fff',
          padding: '18px 14px',
          boxSizing: 'border-box',
          overflowY: 'auto',
          borderRight: '1px solid #1e293b',
        }}
      >
        <div style={{ marginBottom: '18px' }}>
          <h2 style={{ margin: 0, fontSize: '22px', fontWeight: 800 }}>HUTE</h2>
          <p style={{ margin: '6px 0 0', color: '#cbd5e1', fontSize: '13px' }}>
            SME Operating System
          </p>
        </div>

        <nav>
          {menuSections.map((section) => (
            <div key={section.key} style={{ marginBottom: '14px' }}>
              <button
                type="button"
                onClick={() => toggleSection(section.key)}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  padding: '10px 12px',
                  borderRadius: '10px',
                  border: '1px solid #334155',
                  background: '#1e293b',
                  color: '#f8fafc',
                  cursor: 'pointer',
                  fontWeight: 700,
                  fontSize: '14px',
                }}
              >
                {section.label}
              </button>

              {openSections[section.key] ? (
                <div style={{ marginTop: '8px', display: 'grid', gap: '6px' }}>
                  {section.items.map((item) => (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      style={({ isActive }) => ({
                        display: 'block',
                        padding: '10px 12px',
                        borderRadius: '10px',
                        textDecoration: 'none',
                        background: isActive ? '#2563eb' : 'transparent',
                        color: isActive ? '#ffffff' : '#cbd5e1',
                        fontWeight: isActive ? 700 : 500,
                        border: isActive ? '1px solid #3b82f6' : '1px solid transparent',
                      })}
                    >
                      {item.label}
                    </NavLink>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </nav>

        <div style={{ marginTop: '18px' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleLogout}
            style={{ width: '100%' }}
          >
            Logout
          </button>
        </div>
      </aside>

      <main
        style={{
          flex: 1,
          padding: '20px',
          background: '#f8fafc',
          boxSizing: 'border-box',
          overflowX: 'auto',
        }}
      >
        <Outlet />
      </main>
    </div>
  )
}