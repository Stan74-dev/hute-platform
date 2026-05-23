import { useEffect, useState } from 'react'
import API from '../api/client'
import { getTerminalSettings } from '../utils/terminalSettings'

export default function ShiftPage() {
  const [shift, setShift] = useState(null)
  const [lastClosedShift, setLastClosedShift] = useState(null)
  const [openingFloat, setOpeningFloat] = useState('')
  const [actualCash, setActualCash] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const loadShift = async () => {
    try {
      setLoading(true)
      setError('')

      const [currentRes, lastClosedRes] = await Promise.all([
        API.get('/accounts/shift/current/'),
        API.get('/accounts/shift/last-closed/'),
      ])

      setShift(currentRes.data.shift)
      setLastClosedShift(lastClosedRes.data.shift)
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.detail || 'Could not load shift.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadShift()
  }, [])

  const startShift = async () => {
    try {
      setError('')
      setMessage('')

      const terminal = getTerminalSettings()

      const res = await API.post('/accounts/shift/start/', {
        terminal_id: terminal.terminal_id || 'UNKNOWN',
        terminal_name: terminal.terminal_name || terminal.terminal_id || 'UNKNOWN',
        terminal: terminal.terminal_name || terminal.terminal_id || 'UNKNOWN',
        opening_float: openingFloat || '0.00',
      })

      setMessage(res.data.message || res.data.detail || 'Shift started')
      setOpeningFloat('')
      await loadShift()
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.detail || 'Could not start shift.')
    }
  }

  const endShift = async () => {
    try {
      setError('')
      setMessage('')

      const res = await API.post('/accounts/shift/end/', {
        actual_cash: actualCash,
      })

      const closedShift = res.data.shift || res.data

      setMessage(
        `Shift closed. Expected cash: £${closedShift.expected_cash || '0.00'}, actual cash: £${closedShift.actual_cash || '0.00'}, variance: £${closedShift.variance || '0.00'}`
      )
      setActualCash('')
      await loadShift()
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.detail || 'Could not end shift.')
    }
  }

  const downloadShiftPdf = async () => {
    if (!lastClosedShift?.id) {
      setError('No closed shift report available.')
      return
    }

    try {
      setError('')
      const shiftId = lastClosedShift.id || lastClosedShift.shift_id
      const response = await API.get(`/accounts/shift/report-pdf/?shift=${shiftId}`)
      console.log('Shift PDF payload:', response.data)
      alert('Shift report payload prepared successfully.')
    } catch {
      setError('Could not download shift report PDF.')
    }
  }

  return (
    <div>
      <div className="section-header">
        <h2>Cashier Shift</h2>
        <p className="muted-text">
          Start a shift before checkout. End the shift with cash reconciliation.
        </p>
      </div>

      {loading ? <p style={{ marginTop: '16px' }}>Loading shift...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}
      {message ? <p style={{ color: 'green', marginTop: '16px' }}>{message}</p> : null}

      {!shift ? (
        <div className="content-card" style={{ marginTop: '20px' }}>
          <h3>Start Shift</h3>

          <label style={{ marginTop: '12px', display: 'block' }}>Opening Float</label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={openingFloat}
            onChange={(e) => setOpeningFloat(e.target.value)}
            placeholder="e.g. 100.00"
          />

          <button
            type="button"
            className="btn btn-primary"
            style={{ marginTop: '16px' }}
            onClick={startShift}
          >
            Start Shift
          </button>
        </div>
      ) : (
        <div className="card-grid" style={{ marginTop: '20px' }}>
          <div className="content-card">
            <h3>Active Shift</h3>
            <p><strong>Shift ID:</strong> {shift.id}</p>
            <p><strong>Terminal:</strong> {shift.terminal_id}</p>
            <p><strong>Opening Float:</strong> £{shift.opening_float}</p>
            <p><strong>Cash Sales:</strong> £{shift.cash_sales}</p>
            <p><strong>Card Sales:</strong> £{shift.card_sales}</p>
            <p><strong>Expected Cash:</strong> £{shift.expected_cash}</p>
            <p><strong>Opened At:</strong> {shift.opened_at}</p>
            <p><strong>Status:</strong> {shift.status}</p>
          </div>

          <div className="content-card">
            <h3>End Shift</h3>

            <label style={{ marginTop: '12px', display: 'block' }}>Actual Cash Counted</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={actualCash}
              onChange={(e) => setActualCash(e.target.value)}
              placeholder="e.g. 145.50"
            />

            <button
              type="button"
              className="btn btn-danger"
              style={{ marginTop: '16px' }}
              onClick={endShift}
            >
              End Shift
            </button>
          </div>
        </div>
      )}

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Last Closed Shift Report</h3>

        {!lastClosedShift ? (
          <p style={{ marginTop: '12px' }}>No closed shift available yet.</p>
        ) : (
          <>
            <p><strong>Shift ID:</strong> {lastClosedShift.id}</p>
            <p><strong>Terminal:</strong> {lastClosedShift.terminal_id}</p>
            <p><strong>Opening Float:</strong> £{lastClosedShift.opening_float}</p>
            <p><strong>Expected Cash:</strong> £{lastClosedShift.expected_cash}</p>
            <p><strong>Actual Cash:</strong> £{lastClosedShift.actual_cash}</p>
            <p><strong>Cash Sales:</strong> £{lastClosedShift.cash_sales}</p>
            <p><strong>Card Sales:</strong> £{lastClosedShift.card_sales}</p>
            <p><strong>Variance:</strong> £{lastClosedShift.variance}</p>
            <p><strong>Closed At:</strong> {lastClosedShift.closed_at}</p>

            <button
              type="button"
              className="btn btn-secondary"
              style={{ marginTop: '16px' }}
              onClick={downloadShiftPdf}
            >
              Download Shift Report PDF
            </button>
          </>
        )}
      </div>
    </div>
  )
}