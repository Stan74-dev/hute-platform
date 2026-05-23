import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ExecutiveDashboardPage from './pages/ExecutiveDashboardPage'
import HistoricalTrendsPage from './pages/HistoricalTrendsPage'
import DayDetailPage from './pages/DayDetailPage'
import POSPage from './pages/POSPage'
import SalesPage from './pages/SalesPage'
import SalesAnalyticsPage from './pages/SalesAnalyticsPage'
import SaleDetailPage from './pages/SaleDetailPage'
import RefundsPage from './pages/RefundsPage'
import ProductsPage from './pages/ProductsPage'
import WarehousesPage from './pages/WarehousesPage'
import TransfersPage from './pages/TransfersPage'
import PurchaseOrdersPage from './pages/PurchaseOrdersPage'
import GoodsReceivedPage from './pages/GoodsReceivedPage'
import ShiftPage from './pages/ShiftPage'
import AllShiftsPage from './pages/AllShiftsPage'
import ShiftVariancePage from './pages/ShiftVariancePage'
import ShiftSalesReportPage from './pages/ShiftSalesReportPage'
import ShiftDetailPage from './pages/ShiftDetailPage'
import TerminalsPage from './pages/TerminalsPage'
import TerminalActivityPage from './pages/TerminalActivityPage'
import AnomalyDashboardPage from './pages/AnomalyDashboardPage'
import AnomalyCasesPage from './pages/AnomalyCasesPage'
import AnomalyCaseDetailPage from './pages/AnomalyCaseDetailPage'
import DailySummaryPage from './pages/DailySummaryPage'
import AuditTrailPage from './pages/AuditTrailPage'
import UsersPage from './pages/UsersPage'
import FinancePage from './pages/FinancePage'
import TaxSummaryPage from './pages/TaxSummaryPage'

function isAuthenticated() {
  return Boolean(localStorage.getItem('access_token'))
}

function PrivateRoute({ children }) {
  return isAuthenticated() ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />

          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="executive-dashboard" element={<ExecutiveDashboardPage />} />
          <Route path="historical-trends" element={<HistoricalTrendsPage />} />
          <Route path="day-detail" element={<DayDetailPage />} />

          <Route path="pos" element={<POSPage />} />
          <Route path="sales" element={<SalesPage />} />
          <Route path="sales-analytics" element={<SalesAnalyticsPage />} />
          <Route path="sales/:saleId" element={<SaleDetailPage />} />
          <Route path="refunds" element={<RefundsPage />} />

          <Route path="products" element={<ProductsPage />} />
          <Route path="warehouses" element={<WarehousesPage />} />
          <Route path="transfers" element={<TransfersPage />} />
          <Route path="purchase-orders" element={<PurchaseOrdersPage />} />
          <Route path="goods-received" element={<GoodsReceivedPage />} />

          <Route path="shift" element={<ShiftPage />} />
          <Route path="all-shifts" element={<AllShiftsPage />} />
          <Route path="shift-variance" element={<ShiftVariancePage />} />
          <Route path="shift-sales-report" element={<ShiftSalesReportPage />} />
          <Route path="shifts/:shiftId" element={<ShiftDetailPage />} />

          <Route path="terminals" element={<TerminalsPage />} />
          <Route path="terminal-activity" element={<TerminalActivityPage />} />

          <Route path="anomaly-dashboard" element={<AnomalyDashboardPage />} />
          <Route path="anomaly-cases" element={<AnomalyCasesPage />} />
          <Route path="anomaly-cases/:caseId" element={<AnomalyCaseDetailPage />} />

          <Route path="daily-summary" element={<DailySummaryPage />} />
          <Route path="audit-trail" element={<AuditTrailPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="finance" element={<FinancePage />} />
          <Route path="tax-summary" element={<TaxSummaryPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}