import { useEffect, useMemo, useState } from 'react'
import API from '../api/client'

function formatMoney(value) {
  return Number(value || 0).toFixed(2)
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleDateString()
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
              <div key={`${row[labelKey]}-${index}`}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: '12px',
                    marginBottom: '6px',
                    fontSize: '14px',
                  }}
                >
                  <span>{row[labelKey]}</span>
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

export default function FinancePage() {
  const [dashboard, setDashboard] = useState(null)
  const [invoices, setInvoices] = useState([])
  const [payments, setPayments] = useState([])
  const [selectedInvoice, setSelectedInvoice] = useState(null)

  const [invoiceFilter, setInvoiceFilter] = useState('all')

  const [paymentInvoice, setPaymentInvoice] = useState('')
  const [paymentAmount, setPaymentAmount] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('bank_transfer')
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().slice(0, 10))
  const [paymentReference, setPaymentReference] = useState('')
  const [paymentNotes, setPaymentNotes] = useState('')

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [pdfLoadingId, setPdfLoadingId] = useState(null)
  const [exportLoading, setExportLoading] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const safeArray = (value) => (Array.isArray(value) ? value : [])

  const loadFinance = async () => {
    try {
      setLoading(true)
      setError('')
      setSuccess('')

      const [dashboardRes, invoicesRes, paymentsRes] = await Promise.all([
        API.get('/finance/dashboard/'),
        API.get('/finance/invoices/'),
        API.get('/finance/payments/'),
      ])

      const dashboardData = dashboardRes.data || {}
      const invoiceData = safeArray(invoicesRes.data)
      const paymentData = safeArray(paymentsRes.data)

      setDashboard(dashboardData)
      setInvoices(invoiceData)
      setPayments(paymentData)

      if (selectedInvoice) {
        const fresh =
          invoiceData.find((item) => String(item.id) === String(selectedInvoice.id)) ||
          safeArray(dashboardData.recent_invoices).find(
            (item) => String(item.id) === String(selectedInvoice.id)
          ) ||
          null
        setSelectedInvoice(fresh)
      }
    } catch (err) {
      const data = err.response?.data
      if (typeof data === 'string') {
        setError(data)
      } else if (data?.detail) {
        setError(data.detail)
      } else {
        setError('Could not load finance data.')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFinance()
  }, [])

  const dashboardSummary = dashboard?.summary || {
    total_invoices: 0,
    total_invoiced_amount: 0,
    total_paid_amount: 0,
    total_payables: 0,
    overdue_count: 0,
    overdue_amount: 0,
    paid_today: 0,
    payments_today_count: 0,
  }

  const statusBreakdown = dashboard?.status_breakdown || {
    unpaid: 0,
    partial: 0,
    paid: 0,
    overdue: 0,
  }

  const supplierBalances = safeArray(dashboard?.supplier_balances)
  const recentInvoices = safeArray(dashboard?.recent_invoices)
  const recentPayments = safeArray(dashboard?.recent_payments)

  const invoiceSource = useMemo(() => {
    return invoices.length > 0 ? invoices : recentInvoices
  }, [invoices, recentInvoices])

  const filteredInvoices = useMemo(() => {
    if (invoiceFilter === 'all') return invoiceSource
    if (invoiceFilter === 'overdue') {
      return invoiceSource.filter((invoice) => invoice.is_overdue)
    }
    return invoiceSource.filter((invoice) => invoice.status === invoiceFilter)
  }, [invoiceSource, invoiceFilter])

  const selectedInvoicePayments = useMemo(() => {
    if (!selectedInvoice) return []
    return payments.filter(
      (payment) => String(payment.invoice) === String(selectedInvoice.id)
    )
  }, [payments, selectedInvoice])

  const invoiceStatusChartData = useMemo(() => {
    return [
      { label: 'Unpaid', value: Number(statusBreakdown.unpaid || 0) },
      { label: 'Partial', value: Number(statusBreakdown.partial || 0) },
      { label: 'Paid', value: Number(statusBreakdown.paid || 0) },
      { label: 'Overdue', value: Number(statusBreakdown.overdue || 0) },
    ]
  }, [statusBreakdown])

  const supplierBalanceChartData = useMemo(() => {
    return supplierBalances.map((item) => ({
      name: item.supplier_name,
      balance: Number(item.total_balance || 0),
    }))
  }, [supplierBalances])

  const openInvoice = (invoice) => {
    setSelectedInvoice(invoice)
    setPaymentInvoice(String(invoice.id))
    setPaymentAmount(invoice.balance_due ? String(invoice.balance_due) : '')
    setPaymentMethod('bank_transfer')
    setPaymentDate(new Date().toISOString().slice(0, 10))
    setPaymentReference('')
    setPaymentNotes(`Payment for ${invoice.invoice_number}`)
  }

  const resetPaymentForm = () => {
    setPaymentInvoice('')
    setPaymentAmount('')
    setPaymentMethod('bank_transfer')
    setPaymentDate(new Date().toISOString().slice(0, 10))
    setPaymentReference('')
    setPaymentNotes('')
  }

  const recordPayment = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')

    try {
      await API.post('/finance/payments/create/', {
        invoice_id: Number(paymentInvoice),
        amount: paymentAmount,
        payment_method: paymentMethod,
        payment_date: paymentDate,
        reference: paymentReference,
        notes: paymentNotes,
      })

      setSuccess('Payment recorded successfully.')
      resetPaymentForm()
      await loadFinance()
    } catch (err) {
      const data = err.response?.data
      if (typeof data === 'string') {
        setError(data)
      } else if (data?.detail) {
        setError(data.detail)
      } else if (data) {
        setError(JSON.stringify(data))
      } else {
        setError('Could not record payment.')
      }
    } finally {
      setSaving(false)
    }
  }

  const payFullBalance = async () => {
    if (!selectedInvoice) return
    if (Number(selectedInvoice.balance_due || 0) <= 0) return

    setSaving(true)
    setError('')
    setSuccess('')

    try {
      await API.post('/finance/payments/create/', {
        invoice_id: Number(selectedInvoice.id),
        amount: selectedInvoice.balance_due,
        payment_method: paymentMethod,
        payment_date: paymentDate,
        reference: paymentReference,
        notes: `Full payment for ${selectedInvoice.invoice_number}`,
      })

      setSuccess('Full payment recorded successfully.')
      await loadFinance()
    } catch (err) {
      const data = err.response?.data
      if (typeof data === 'string') {
        setError(data)
      } else if (data?.detail) {
        setError(data.detail)
      } else if (data) {
        setError(JSON.stringify(data))
      } else {
        setError('Could not complete full payment.')
      }
    } finally {
      setSaving(false)
    }
  }

  const downloadInvoicePdf = async (invoice) => {
    try {
      setPdfLoadingId(invoice.id)
      setError('')

      const response = await API.get(`/finance/invoices/${invoice.id}/pdf/`, {
        responseType: 'blob',
      })

      downloadBlobFile(
        response.data,
        `${invoice.invoice_number || `invoice-${invoice.id}`}.pdf`
      )
    } catch (_err) {
      setError('Could not download invoice PDF.')
    } finally {
      setPdfLoadingId(null)
    }
  }

  const exportCsv = async (endpoint, filename, key) => {
    try {
      setExportLoading(key)
      setError('')
      const response = await API.get(endpoint, { responseType: 'blob' })
      downloadBlobFile(response.data, filename)
    } catch (_err) {
      setError('Could not export CSV.')
    } finally {
      setExportLoading('')
    }
  }

  return (
    <div>
      <div
        className="section-header"
        style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', alignItems: 'start', flexWrap: 'wrap' }}
      >
        <div>
          <h2>Finance Dashboard</h2>
          <p className="muted-text">
            Live payables, supplier balances, overdue invoices, charts, and export tools.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => exportCsv('/finance/export/summary/', 'finance_summary.csv', 'summary')}
            disabled={exportLoading === 'summary'}
          >
            {exportLoading === 'summary' ? 'Exporting...' : 'Export Summary'}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => exportCsv('/finance/export/invoices/', 'finance_invoices.csv', 'invoices')}
            disabled={exportLoading === 'invoices'}
          >
            {exportLoading === 'invoices' ? 'Exporting...' : 'Export Invoices'}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => exportCsv('/finance/export/payments/', 'finance_payments.csv', 'payments')}
            disabled={exportLoading === 'payments'}
          >
            {exportLoading === 'payments' ? 'Exporting...' : 'Export Payments'}
          </button>
        </div>
      </div>

      {loading ? <p>Loading finance dashboard...</p> : null}
      {error ? <p className="error-text">{error}</p> : null}
      {success ? <p style={{ color: 'green' }}>{success}</p> : null}

      <div className="stats-grid" style={{ marginTop: '18px' }}>
        <div className="stat-card">
          <span>Total Payables</span>
          <strong>£{formatMoney(dashboardSummary.total_payables)}</strong>
        </div>
        <div className="stat-card">
          <span>Paid Today</span>
          <strong>£{formatMoney(dashboardSummary.paid_today)}</strong>
        </div>
        <div className="stat-card">
          <span>Overdue Invoices</span>
          <strong>{dashboardSummary.overdue_count}</strong>
        </div>
        <div className="stat-card">
          <span>Overdue Amount</span>
          <strong>£{formatMoney(dashboardSummary.overdue_amount)}</strong>
        </div>
      </div>

      <div className="stats-grid" style={{ marginTop: '18px' }}>
        <div className="stat-card">
          <span>Total Invoices</span>
          <strong>{dashboardSummary.total_invoices}</strong>
        </div>
        <div className="stat-card">
          <span>Total Invoiced</span>
          <strong>£{formatMoney(dashboardSummary.total_invoiced_amount)}</strong>
        </div>
        <div className="stat-card">
          <span>Total Paid</span>
          <strong>£{formatMoney(dashboardSummary.total_paid_amount)}</strong>
        </div>
        <div className="stat-card">
          <span>Payments Today</span>
          <strong>{dashboardSummary.payments_today_count}</strong>
        </div>
      </div>

      <div className="card-grid" style={{ marginTop: '20px' }}>
        <SimpleBarChart
          title="Invoice Status Chart"
          rows={invoiceStatusChartData}
          valueKey="value"
          labelKey="label"
        />
        <SimpleBarChart
          title="Supplier Balance Chart"
          rows={supplierBalanceChartData}
          valueKey="balance"
          labelKey="name"
          money
        />
      </div>

      <div className="card-grid" style={{ marginTop: '20px' }}>
        <div className="content-card">
          <h3>Invoice Status Breakdown</h3>
          <div className="table-wrap" style={{ marginTop: '12px' }}>
            <table>
              <thead>
                <tr>
                  <th>Unpaid</th>
                  <th>Partial</th>
                  <th>Paid</th>
                  <th>Overdue</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{statusBreakdown.unpaid}</td>
                  <td>{statusBreakdown.partial}</td>
                  <td>{statusBreakdown.paid}</td>
                  <td>{statusBreakdown.overdue}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="content-card">
          <h3>Top Supplier Balances</h3>
          <div className="table-wrap" style={{ marginTop: '12px' }}>
            <table>
              <thead>
                <tr>
                  <th>Supplier</th>
                  <th>Invoices</th>
                  <th>Invoiced</th>
                  <th>Paid</th>
                  <th>Balance</th>
                </tr>
              </thead>
              <tbody>
                {supplierBalances.map((row) => (
                  <tr key={row.supplier_id}>
                    <td>{row.supplier_name}</td>
                    <td>{row.invoice_count}</td>
                    <td>£{formatMoney(row.total_invoiced)}</td>
                    <td>£{formatMoney(row.total_paid)}</td>
                    <td>£{formatMoney(row.total_balance)}</td>
                  </tr>
                ))}
                {supplierBalances.length === 0 ? (
                  <tr>
                    <td colSpan="5">No supplier balances found.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="card-grid" style={{ marginTop: '20px' }}>
        <div className="content-card">
          <div
            className="card-header-row"
            style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', alignItems: 'end' }}
          >
            <div>
              <h3>Supplier Invoices</h3>
              <p className="muted-text">Click a row or use Open / PDF.</p>
            </div>

            <div style={{ minWidth: '220px' }}>
              <label>Filter</label>
              <select
                value={invoiceFilter}
                onChange={(e) => setInvoiceFilter(e.target.value)}
              >
                <option value="all">All</option>
                <option value="unpaid">Unpaid</option>
                <option value="partial">Partial</option>
                <option value="paid">Paid</option>
                <option value="overdue">Overdue</option>
              </select>
            </div>
          </div>

          <div className="table-wrap" style={{ marginTop: '12px' }}>
            <table>
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>PO Number</th>
                  <th>Supplier</th>
                  <th>Total</th>
                  <th>Paid</th>
                  <th>Balance</th>
                  <th>Status</th>
                  <th>Due</th>
                  <th>Open</th>
                  <th>PDF</th>
                </tr>
              </thead>
              <tbody>
                {filteredInvoices.map((invoice) => (
                  <tr
                    key={invoice.id}
                    onClick={() => openInvoice(invoice)}
                    style={{
                      cursor: 'pointer',
                      background:
                        selectedInvoice?.id === invoice.id ? '#f5f9ff' : 'transparent',
                    }}
                  >
                    <td>{invoice.invoice_number}</td>
                    <td>{invoice.purchase_order_number || invoice.po_number || '-'}</td>
                    <td>{invoice.supplier_name}</td>
                    <td>£{formatMoney(invoice.total_amount)}</td>
                    <td>£{formatMoney(invoice.amount_paid)}</td>
                    <td>£{formatMoney(invoice.balance_due)}</td>
                    <td>{invoice.status}</td>
                    <td>{formatDate(invoice.due_date)}</td>
                    <td>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          openInvoice(invoice)
                        }}
                        className="btn btn-secondary"
                      >
                        Open
                      </button>
                    </td>
                    <td>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          downloadInvoicePdf(invoice)
                        }}
                        disabled={pdfLoadingId === invoice.id}
                        className="btn btn-primary"
                      >
                        {pdfLoadingId === invoice.id ? '...' : 'PDF'}
                      </button>
                    </td>
                  </tr>
                ))}
                {filteredInvoices.length === 0 ? (
                  <tr>
                    <td colSpan="10">No invoices found.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>

        <div className="content-card">
          <div
            className="card-header-row"
            style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', alignItems: 'start' }}
          >
            <div>
              <h3>Invoice Detail</h3>
              <p className="muted-text">Selected invoice details and payment history.</p>
            </div>

            {selectedInvoice ? (
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => downloadInvoicePdf(selectedInvoice)}
                  disabled={pdfLoadingId === selectedInvoice.id}
                >
                  {pdfLoadingId === selectedInvoice.id ? 'Downloading...' : 'Download PDF'}
                </button>

                {Number(selectedInvoice.balance_due || 0) > 0 ? (
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={payFullBalance}
                    disabled={saving}
                  >
                    Pay Full Balance
                  </button>
                ) : null}
              </div>
            ) : null}
          </div>

          {!selectedInvoice ? (
            <div className="empty-state" style={{ marginTop: '16px' }}>
              Select an invoice from the list.
            </div>
          ) : (
            <div style={{ marginTop: '16px' }}>
              <p><strong>Invoice Number:</strong> {selectedInvoice.invoice_number}</p>
              <p><strong>PO Number:</strong> {selectedInvoice.purchase_order_number || selectedInvoice.po_number || '-'}</p>
              <p><strong>Supplier:</strong> {selectedInvoice.supplier_name}</p>
              <p><strong>Invoice Date:</strong> {formatDate(selectedInvoice.invoice_date)}</p>
              <p><strong>Due Date:</strong> {formatDate(selectedInvoice.due_date)}</p>
              <p><strong>Status:</strong> {selectedInvoice.status}</p>
              <p><strong>Total Amount:</strong> £{formatMoney(selectedInvoice.total_amount)}</p>
              <p><strong>Amount Paid:</strong> £{formatMoney(selectedInvoice.amount_paid)}</p>
              <p><strong>Balance Due:</strong> £{formatMoney(selectedInvoice.balance_due)}</p>
              <p><strong>Notes:</strong> {selectedInvoice.notes || '-'}</p>

              <div style={{ marginTop: '18px' }}>
                <h4>Payment History</h4>
                <div className="table-wrap" style={{ marginTop: '10px' }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Reference</th>
                        <th>Date</th>
                        <th>Method</th>
                        <th>Amount</th>
                        <th>Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedInvoicePayments.map((payment) => (
                        <tr key={payment.id}>
                          <td>{payment.reference || payment.payment_number || '-'}</td>
                          <td>{formatDate(payment.payment_date)}</td>
                          <td>{payment.payment_method}</td>
                          <td>£{formatMoney(payment.amount)}</td>
                          <td>{payment.notes || '-'}</td>
                        </tr>
                      ))}
                      {selectedInvoicePayments.length === 0 ? (
                        <tr>
                          <td colSpan="5">No payments recorded yet.</td>
                        </tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="card-grid" style={{ marginTop: '20px' }}>
        <div className="content-card">
          <h3>Record Supplier Payment</h3>

          <form onSubmit={recordPayment} style={{ marginTop: '12px' }}>
            <label>Invoice</label>
            <select
              value={paymentInvoice}
              onChange={(e) => setPaymentInvoice(e.target.value)}
              required
            >
              <option value="">Select invoice</option>
              {invoiceSource
                .filter((invoice) => invoice.status !== 'paid')
                .map((invoice) => (
                  <option key={invoice.id} value={invoice.id}>
                    {invoice.invoice_number} - {invoice.supplier_name} - £{formatMoney(invoice.balance_due)}
                  </option>
                ))}
            </select>

            <label style={{ marginTop: '12px', display: 'block' }}>Amount</label>
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={paymentAmount}
              onChange={(e) => setPaymentAmount(e.target.value)}
              required
            />

            <label style={{ marginTop: '12px', display: 'block' }}>Payment Method</label>
            <select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
              required
            >
              <option value="bank_transfer">Bank Transfer</option>
              <option value="cash">Cash</option>
              <option value="ecocash">EcoCash</option>
              <option value="card">Card</option>
              <option value="other">Other</option>
            </select>

            <label style={{ marginTop: '12px', display: 'block' }}>Payment Date</label>
            <input
              type="date"
              value={paymentDate}
              onChange={(e) => setPaymentDate(e.target.value)}
              required
            />

            <label style={{ marginTop: '12px', display: 'block' }}>Reference</label>
            <input
              value={paymentReference}
              onChange={(e) => setPaymentReference(e.target.value)}
              placeholder="Transfer ref / bank ref"
            />

            <label style={{ marginTop: '12px', display: 'block' }}>Notes</label>
            <textarea
              value={paymentNotes}
              onChange={(e) => setPaymentNotes(e.target.value)}
              rows="3"
            />

            <div style={{ display: 'flex', gap: '10px', marginTop: '16px', flexWrap: 'wrap' }}>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? 'Saving...' : 'Record Payment'}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={resetPaymentForm}
              >
                Clear
              </button>
            </div>
          </form>
        </div>

        <div className="content-card">
          <h3>Recent Activity</h3>

          <h4 style={{ marginTop: '8px' }}>Recent Invoices</h4>
          <div className="table-wrap" style={{ marginTop: '10px' }}>
            <table>
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>Supplier</th>
                  <th>Total</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {recentInvoices.map((invoice) => (
                  <tr key={invoice.id}>
                    <td>{invoice.invoice_number}</td>
                    <td>{invoice.supplier_name}</td>
                    <td>£{formatMoney(invoice.total_amount)}</td>
                    <td>{invoice.status}</td>
                  </tr>
                ))}
                {recentInvoices.length === 0 ? (
                  <tr>
                    <td colSpan="4">No recent invoices.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>

          <h4 style={{ marginTop: '20px' }}>Recent Payments</h4>
          <div className="table-wrap" style={{ marginTop: '10px' }}>
            <table>
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Supplier</th>
                  <th>Date</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                {recentPayments.map((payment) => (
                  <tr key={payment.id}>
                    <td>{payment.reference || payment.payment_number || '-'}</td>
                    <td>{payment.supplier_name || '-'}</td>
                    <td>{formatDate(payment.payment_date)}</td>
                    <td>£{formatMoney(payment.amount)}</td>
                  </tr>
                ))}
                {recentPayments.length === 0 ? (
                  <tr>
                    <td colSpan="4">No recent payments.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}