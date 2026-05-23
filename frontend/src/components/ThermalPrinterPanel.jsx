import { useEffect, useState } from 'react'
import { disconnectQz, findPrinters, printTestReceipt } from '../utils/thermalPrinter'

const STORAGE_KEY = 'hute_default_printer'

export default function ThermalPrinterPanel() {
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [printers, setPrinters] = useState([])
  const [selectedPrinter, setSelectedPrinter] = useState(
    localStorage.getItem(STORAGE_KEY) || ''
  )

  const loadPrinters = async () => {
    try {
      setLoading(true)
      setError('')
      setSuccess('')

      const list = await findPrinters()
      setPrinters(list)

      if (!selectedPrinter && list.length > 0) {
        setSelectedPrinter(list[0])
      }
    } catch (err) {
      setError(
        err?.message ||
        'Could not connect to QZ Tray or list printers.'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPrinters()

    return () => {
      disconnectQz().catch(() => {})
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const savePrinter = () => {
    if (!selectedPrinter) {
      setError('Select a printer first.')
      return
    }

    localStorage.setItem(STORAGE_KEY, selectedPrinter)
    setSuccess('Default thermal printer saved.')
    setError('')
  }

  const handleTestPrint = async () => {
    try {
      setTesting(true)
      setError('')
      setSuccess('')

      if (!selectedPrinter) {
        throw new Error('Select a printer first.')
      }

      await printTestReceipt(selectedPrinter)
      setSuccess('Test receipt sent to printer.')
    } catch (err) {
      setError(err?.message || 'Could not print test receipt.')
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="content-card" style={{ marginTop: '20px' }}>
      <h3>Thermal Printer</h3>

      {loading ? <p style={{ marginTop: '10px' }}>Loading printers...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '10px' }}>{error}</p> : null}
      {success ? <p style={{ marginTop: '10px', color: 'green' }}>{success}</p> : null}

      <div style={{ marginTop: '12px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <select
          value={selectedPrinter}
          onChange={(e) => setSelectedPrinter(e.target.value)}
          style={{ minWidth: '320px' }}
        >
          <option value="">Select printer</option>
          {printers.map((printer) => (
            <option key={printer} value={printer}>
              {printer}
            </option>
          ))}
        </select>

        <button type="button" className="btn btn-secondary" onClick={loadPrinters}>
          Refresh Printers
        </button>

        <button
          type="button"
          className="btn btn-primary"
          onClick={savePrinter}
          disabled={!selectedPrinter}
        >
          Save Default Printer
        </button>

        <button
          type="button"
          className="btn btn-secondary"
          onClick={handleTestPrint}
          disabled={!selectedPrinter || testing}
        >
          {testing ? 'Printing Test...' : 'Test Print'}
        </button>
      </div>

      <p className="muted-text" style={{ marginTop: '12px' }}>
        Install QZ Tray on the POS machine and make sure the thermal printer is visible in Windows before using this.
      </p>
    </div>
  )
}