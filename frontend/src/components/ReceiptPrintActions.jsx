import { useMemo, useState } from 'react'
import { printThermalReceipt } from '../utils/thermalPrinter'

const STORAGE_KEY = 'hute_default_printer'

export default function ReceiptPrintActions({ sale }) {
  const [printing, setPrinting] = useState(false)
  const [message, setMessage] = useState('')
  const printerName = useMemo(() => localStorage.getItem(STORAGE_KEY) || '', [])

  const handlePrint = async () => {
    try {
      setPrinting(true)
      setMessage('')

      if (!printerName) {
        throw new Error('No default thermal printer has been saved.')
      }

      await printThermalReceipt(printerName, sale)
      setMessage('Receipt sent to printer.')
    } catch (err) {
      setMessage(err?.message || 'Could not print receipt.')
    } finally {
      setPrinting(false)
    }
  }

  return (
    <div style={{ marginTop: '14px' }}>
      <button
        type="button"
        className="btn btn-primary"
        onClick={handlePrint}
        disabled={printing}
      >
        {printing ? 'Printing...' : 'Print Thermal Receipt'}
      </button>

      {message ? (
        <p style={{ marginTop: '10px' }}>{message}</p>
      ) : null}
    </div>
  )
}