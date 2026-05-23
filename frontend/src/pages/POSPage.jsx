import { useEffect, useMemo, useState } from 'react'
import API from '../api/client'
import {
  buildOfflineReceiptFromPayload,
  getUnsyncedSales,
  saveOfflineSale,
} from '../utils/offlineSales'
import { syncOfflineSales } from '../utils/syncService'
import { printReceipt } from '../utils/receiptPrinter'
import { checkLocalPrinterBridge, printReceiptViaBridge } from '../utils/localPrinter'
import { getTerminalSettings, saveTerminalSettings } from '../utils/terminalSettings'
import { registerTerminalWithBackend } from '../utils/terminalApi'
import { printThermalReceipt } from '../utils/thermalPrinter'
import ThermalPrinterPanel from '../components/ThermalPrinterPanel'
import ReceiptPrintActions from '../components/ReceiptPrintActions'

function formatMoney(value) {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0.00'
  return num.toFixed(2)
}

function numberValue(value) {
  const num = Number(value || 0)
  return Number.isNaN(num) ? 0 : num
}

function isNetworkError(err) {
  return !err.response
}

function getProductTaxRatePercent(product) {
  const direct =
    product.tax_rate_percent ??
    product.rate_percent ??
    product.tax_percent ??
    product.vat_rate ??
    product.tax_rate?.rate_percent

  if (direct !== null && direct !== undefined && direct !== '') {
    return numberValue(direct)
  }

  const taxName = String(product.tax_rate_name || product.tax_name || product.tax || '').toLowerCase()

  if (
    taxName.includes('no tax') ||
    taxName.includes('zero') ||
    taxName.includes('exempt')
  ) {
    return 0
  }

  if (taxName.includes('standard')) {
    return 20
  }

  return 0
}

function calculateLineSubtotal(item) {
  return numberValue(item.unit_price) * numberValue(item.quantity)
}

function calculateLineTax(item) {
  return calculateLineSubtotal(item) * (numberValue(item.tax_rate_percent) / 100)
}

function calculateLineTotal(item) {
  return calculateLineSubtotal(item) + calculateLineTax(item)
}

export default function POSPage() {
  const initialTerminal = getTerminalSettings()

  const [products, setProducts] = useState([])
  const [warehouses, setWarehouses] = useState([])
  const [selectedWarehouse, setSelectedWarehouse] = useState('')
  const [cart, setCart] = useState([])
  const [paymentMethod, setPaymentMethod] = useState('cash')

  const [terminalId, setTerminalId] = useState(initialTerminal.terminal_id)
  const [terminalName, setTerminalName] = useState(initialTerminal.terminal_name)
  const [printMode, setPrintMode] = useState(initialTerminal.print_mode || 'browser')
  const [autoPrint, setAutoPrint] = useState(Boolean(initialTerminal.auto_print))
  const [bridgeReady, setBridgeReady] = useState(false)
  const [terminalRegistered, setTerminalRegistered] = useState(false)
  const [terminalBlocked, setTerminalBlocked] = useState(false)
  const [shift, setShift] = useState(null)

  const [loading, setLoading] = useState(true)
  const [checkingOut, setCheckingOut] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [offlineCount, setOfflineCount] = useState(0)
  const [lastReceipt, setLastReceipt] = useState(null)

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const refreshOfflineCount = () => {
    setOfflineCount(getUnsyncedSales().length)
  }

  const loadShift = async () => {
    try {
      const { data } = await API.get('/accounts/shift/current/')
      setShift(data.shift)
    } catch {
      setShift(null)
    }
  }

  const persistTerminalSettings = (updates = {}) => {
    const saved = saveTerminalSettings({
      terminal_id: terminalId,
      terminal_name: terminalName,
      print_mode: printMode,
      auto_print: autoPrint,
      ...updates,
    })

    setTerminalId(saved.terminal_id)
    setTerminalName(saved.terminal_name)
    setPrintMode(saved.print_mode)
    setAutoPrint(Boolean(saved.auto_print))
    return saved
  }

  const registerTerminal = async (settingsOverride = null, showSuccess = false) => {
    try {
      const settings = settingsOverride || {
        terminal_id: terminalId,
        terminal_name: terminalName,
        print_mode: printMode,
        auto_print: autoPrint,
      }

      await registerTerminalWithBackend(settings)
      setTerminalRegistered(true)
      setTerminalBlocked(false)

      if (showSuccess) {
        setSuccess('Terminal registered with backend.')
      }
    } catch (err) {
      setTerminalRegistered(false)
      const detail = err.response?.data?.detail || 'Could not register terminal with backend.'

      if (err.response?.status === 403) {
        setTerminalBlocked(true)
      }

      if (showSuccess) {
        setError(detail)
      }
    }
  }

  const getWarehouseName = (warehouseId) => {
    const found = warehouses.find((w) => String(w.id) === String(warehouseId))
    return found?.name || '-'
  }

  const loadPOSData = async () => {
    try {
      setLoading(true)
      setError('')

      const [productsRes, warehousesRes] = await Promise.all([
        API.get('/inventory/products/'),
        API.get('/inventory/warehouses/'),
      ])

      const productsData = Array.isArray(productsRes.data) ? productsRes.data : []
      const warehousesData = Array.isArray(warehousesRes.data) ? warehousesRes.data : []

      setProducts(productsData)
      setWarehouses(warehousesData)

      if (!selectedWarehouse && warehousesData.length > 0) {
        setSelectedWarehouse(String(warehousesData[0].id))
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load POS data.')
    } finally {
      setLoading(false)
    }
  }

  const checkBridge = async () => {
    try {
      await checkLocalPrinterBridge()
      setBridgeReady(true)
      return true
    } catch {
      setBridgeReady(false)
      return false
    }
  }

  useEffect(() => {
    loadPOSData()
    loadShift()
    refreshOfflineCount()
    checkBridge()
    registerTerminal()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const handleOnline = async () => {
      await registerTerminal()
      await loadShift()
      if (!terminalBlocked) {
        await handleSyncOfflineSales(false)
      }
    }

    window.addEventListener('online', handleOnline)
    return () => window.removeEventListener('online', handleOnline)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [terminalId, terminalName, printMode, autoPrint, terminalBlocked])

  const addToCart = (product) => {
    setError('')
    setSuccess('')

    const taxRatePercent = getProductTaxRatePercent(product)

    setCart((prev) => {
      const existing = prev.find((item) => item.product === product.id)

      if (existing) {
        return prev.map((item) =>
          item.product === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        )
      }

      return [
        ...prev,
        {
          product: product.id,
          product_name: product.name,
          product_sku: product.sku,
          unit_price: numberValue(product.selling_price),
          tax_rate_name: product.tax_rate_name || product.tax_name || product.tax || '',
          tax_rate_percent: taxRatePercent,
          quantity: 1,
        },
      ]
    })
  }

  const updateCartQuantity = (productId, quantity) => {
    const parsedQty = Number(quantity)

    if (parsedQty <= 0 || Number.isNaN(parsedQty)) {
      setCart((prev) => prev.filter((item) => item.product !== productId))
      return
    }

    setCart((prev) =>
      prev.map((item) =>
        item.product === productId
          ? { ...item, quantity: parsedQty }
          : item
      )
    )
  }

  const removeFromCart = (productId) => {
    setCart((prev) => prev.filter((item) => item.product !== productId))
  }

  const clearCart = () => {
    setCart([])
  }

  const cartSubtotal = useMemo(() => {
    return cart.reduce((sum, item) => sum + calculateLineSubtotal(item), 0)
  }, [cart])

  const cartTax = useMemo(() => {
    return cart.reduce((sum, item) => sum + calculateLineTax(item), 0)
  }, [cart])

  const cartGrandTotal = cartSubtotal + cartTax

  const performPrint = async (receipt, options = {}) => {
    const force = Boolean(options.force)

    if (!force && !autoPrint) return

    const enrichedReceipt = {
      ...receipt,
      terminal_id: terminalId,
      terminal_name: terminalName,
      business_name: 'HUTE POS',
    }

    if (printMode === 'qz') {
      const printerName = localStorage.getItem('hute_default_printer') || ''

      if (!printerName) {
        if (force) {
          setError('No QZ Tray thermal printer has been saved.')
        }
        return
      }

      try {
        await printThermalReceipt(printerName, enrichedReceipt)
        return
      } catch (err) {
        setError(err?.message || 'QZ Tray printing failed.')
        return
      }
    }

    if (printMode === 'bridge') {
      const ready = await checkBridge()

      if (!ready) {
        setError('Print bridge is not running. Falling back to browser print.')
        printReceipt(enrichedReceipt)
        return
      }

      try {
        await printReceiptViaBridge(enrichedReceipt)
        return
      } catch {
        setError('Bridge print failed. Falling back to browser print.')
        printReceipt(enrichedReceipt)
        return
      }
    }

    printReceipt(enrichedReceipt)
  }

  const handleCheckout = async () => {
    setError('')
    setSuccess('')

    if (terminalBlocked) {
      setError('This terminal is inactive and cannot submit sales. Please contact an administrator.')
      return
    }

    if (!shift) {
      setError('No active shift. Start a shift before checkout.')
      return
    }

    if (shift.terminal_id && shift.terminal_id !== terminalId) {
      setError('The active shift belongs to a different terminal.')
      return
    }

    if (!selectedWarehouse) {
      setError('Please select a warehouse.')
      return
    }

    if (!cart.length) {
      setError('Cart is empty.')
      return
    }

    const payload = {
      warehouse: Number(selectedWarehouse),
      payment_method: paymentMethod,
      terminal: {
        terminal_id: terminalId,
        terminal_name: terminalName,
        preferred_print_mode: printMode,
        auto_print: autoPrint,
      },
      items: cart.map((item) => ({
        product: item.product,
        product_name: item.product_name,
        product_sku: item.product_sku,
        quantity: Number(item.quantity),
        unit_price: Number(item.unit_price),
        tax_rate_percent: Number(item.tax_rate_percent || 0),
      })),
    }

    try {
      setCheckingOut(true)

      const { data } = await API.post('/sales/checkout/', {
        warehouse: payload.warehouse,
        payment_method: payload.payment_method,
        terminal: payload.terminal,
        items: payload.items.map((item) => ({
          product: item.product,
          quantity: item.quantity,
        })),
      })

      const sale = data.sale || data
      const receiptItems = Array.isArray(sale.items) ? sale.items : payload.items

      const subtotal = numberValue(
        sale.subtotal_amount ??
          data.subtotal_amount ??
          data.subtotal ??
          cartSubtotal
      )

      const taxTotal = numberValue(
        sale.tax_amount ??
          data.tax_amount ??
          data.tax_total ??
          cartTax
      )

      const grandTotal = numberValue(
        sale.total_amount ??
          data.total_amount ??
          data.grand_total ??
          subtotal + taxTotal
      )

      const receipt = {
        receipt_number: sale.receipt_number || data.receipt_number,
        created_at: sale.created_at || data.created_at,
        warehouse_name: sale.warehouse_name || getWarehouseName(selectedWarehouse),
        payment_method: sale.payment_method || paymentMethod,
        subtotal,
        subtotal_amount: subtotal,
        tax_total: taxTotal,
        tax_amount: taxTotal,
        grand_total: grandTotal,
        total_amount: grandTotal,
        is_offline: false,
        terminal_id: terminalId,
        terminal_name: terminalName,
        shift_id: sale.shift || data.shift,
        cashier_username: sale.cashier_username || data.cashier_username || shift?.cashier_username || '',
        items: receiptItems.map((item) => {
          const qty = numberValue(item.quantity)
          const unitPrice = numberValue(item.unit_price)
          const itemSubtotal = numberValue(item.line_subtotal ?? unitPrice * qty)
          const itemTax = numberValue(item.tax_amount)
          const itemTotal = numberValue(item.line_total ?? itemSubtotal + itemTax)

          return {
            name: item.product_name || item.name,
            product_name: item.product_name || item.name,
            product_sku: item.product_sku || item.sku || '',
            quantity: qty,
            unit_price: unitPrice,
            tax_rate_percent: numberValue(item.tax_rate_percent),
            tax_amount: itemTax,
            line_subtotal: itemSubtotal,
            line_total: itemTotal,
          }
        }),
      }

      setLastReceipt(receipt)
      setSuccess(`Sale completed online. Shift ID: ${receipt.shift_id || '-'}`)
      clearCart()
      await performPrint(receipt)
      await loadShift()
      refreshOfflineCount()
    } catch (err) {
      const detail = err.response?.data?.detail || 'Checkout failed.'

      if (err.response?.status === 403) {
        setError(detail)
        if (detail.toLowerCase().includes('inactive')) {
          setTerminalBlocked(true)
        }
        if (detail.toLowerCase().includes('shift')) {
          await loadShift()
        }
        return
      }

      if (isNetworkError(err)) {
        const offlineSale = saveOfflineSale(payload)
        refreshOfflineCount()

        const offlineReceipt = buildOfflineReceiptFromPayload(
          offlineSale,
          getWarehouseName(selectedWarehouse)
        )

        const enrichedOfflineReceipt = {
          ...offlineReceipt,
          subtotal: cartSubtotal,
          subtotal_amount: cartSubtotal,
          tax_total: cartTax,
          tax_amount: cartTax,
          grand_total: cartGrandTotal,
          total_amount: cartGrandTotal,
          terminal_id: terminalId,
          terminal_name: terminalName,
          cashier_username: shift?.cashier_username || '',
          items: payload.items.map((item) => {
            const cartItem = cart.find((row) => row.product === item.product) || item
            return {
              name: item.product_name,
              product_name: item.product_name,
              product_sku: item.product_sku,
              quantity: item.quantity,
              unit_price: item.unit_price,
              tax_rate_percent: item.tax_rate_percent,
              tax_amount: calculateLineTax(cartItem),
              line_subtotal: calculateLineSubtotal(cartItem),
              line_total: calculateLineTotal(cartItem),
            }
          }),
        }

        setLastReceipt(enrichedOfflineReceipt)
        setSuccess('No network connection. Sale saved offline and will sync automatically.')
        clearCart()
        await performPrint(enrichedOfflineReceipt)
        return
      }

      setError(detail)
    } finally {
      setCheckingOut(false)
    }
  }

  const handleSyncOfflineSales = async (showSuccess = true) => {
    setError('')
    setSuccess('')

    if (terminalBlocked) {
      setError('This terminal is inactive and cannot sync offline sales.')
      return
    }

    if (!shift) {
      setError('No active shift. Start a shift before syncing offline sales.')
      return
    }

    if (!navigator.onLine) {
      setError('You are offline. Reconnect to sync offline sales.')
      return
    }

    try {
      setSyncing(true)
      const result = await syncOfflineSales()
      refreshOfflineCount()

      if (showSuccess) {
        if (result.total === 0) {
          setSuccess('No offline sales to sync.')
        } else {
          setSuccess(`Sync complete. Synced: ${result.synced}, Failed: ${result.failed}.`)
        }
      }
    } catch (err) {
      setError(err.message || 'Could not sync offline sales.')
    } finally {
      setSyncing(false)
    }
  }

  const handlePrintLastReceipt = async () => {
    if (!lastReceipt) {
      setError('No receipt available to print.')
      return
    }

    try {
      await performPrint(lastReceipt, { force: true })
    } catch {
      setError('Could not print receipt.')
    }
  }

  return (
    <div>
      <div className="section-header">
        <h2>POS Checkout</h2>
        <p className="muted-text">
          Every sale must belong to an active shift for this terminal.
        </p>
      </div>

      {terminalBlocked ? (
        <div style={{ background: '#dc2626', color: '#fff', padding: '10px 12px', borderRadius: '8px', marginTop: '16px' }}>
          This terminal is inactive and cannot be used. Please contact an administrator.
        </div>
      ) : null}

      {!shift ? (
        <div style={{ background: '#f59e0b', color: '#fff', padding: '10px 12px', borderRadius: '8px', marginTop: '16px' }}>
          No active shift. Go to the Shift page and start a shift before checkout.
        </div>
      ) : null}

      {loading ? <p style={{ marginTop: '16px' }}>Loading POS...</p> : null}
      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}
      {success ? <p style={{ color: 'green', marginTop: '16px' }}>{success}</p> : null}

      <div className="stats-grid" style={{ marginTop: '18px' }}>
        <div className="stat-card"><span>Products</span><strong>{products.length}</strong></div>
        <div className="stat-card"><span>Warehouses</span><strong>{warehouses.length}</strong></div>
        <div className="stat-card"><span>Cart Items</span><strong>{cart.length}</strong></div>
        <div className="stat-card"><span>Offline Queue</span><strong>{offlineCount}</strong></div>
      </div>

      <div className="card-grid" style={{ marginTop: '20px' }}>
        <div className="content-card">
          <h3>Terminal Settings</h3>

          <label style={{ marginTop: '12px', display: 'block' }}>Terminal ID</label>
          <input value={terminalId} readOnly />

          <label style={{ marginTop: '12px', display: 'block' }}>Terminal Name</label>
          <input
            value={terminalName}
            onChange={(e) => setTerminalName(e.target.value)}
            onBlur={() => persistTerminalSettings()}
            placeholder="e.g. Front Counter POS"
            disabled={terminalBlocked}
          />

          <label style={{ marginTop: '12px', display: 'block' }}>Print Mode</label>
          <select
            value={printMode}
            onChange={(e) => {
              setPrintMode(e.target.value)
              persistTerminalSettings({ print_mode: e.target.value })
            }}
            disabled={terminalBlocked}
          >
            <option value="browser">Browser Print Dialog</option>
            <option value="bridge">Local Print Bridge</option>
            <option value="qz">QZ Tray Thermal Printer</option>
          </select>

          <label style={{ marginTop: '12px', display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              type="checkbox"
              checked={autoPrint}
              onChange={(e) => {
                setAutoPrint(e.target.checked)
                persistTerminalSettings({ auto_print: e.target.checked })
              }}
              disabled={terminalBlocked}
            />
            Auto-print receipt after checkout
          </label>

          <div style={{ marginTop: '10px', fontSize: '13px', color: bridgeReady ? 'green' : '#666' }}>
            Bridge status: {bridgeReady ? 'Connected' : 'Not connected'}
          </div>

          <div style={{ marginTop: '6px', fontSize: '13px', color: terminalRegistered ? 'green' : '#666' }}>
            Backend terminal status: {terminalBlocked ? 'Blocked' : terminalRegistered ? 'Registered' : 'Not registered'}
          </div>

          <div style={{ marginTop: '6px', fontSize: '13px', color: shift ? 'green' : '#666' }}>
            Shift status: {shift ? `Open (Shift ${shift.id})` : 'No active shift'}
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: '16px', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={async () => {
                await checkBridge()
                setSuccess('Bridge status checked.')
              }}
            >
              Check Bridge
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              onClick={async () => {
                const saved = persistTerminalSettings()
                await registerTerminal(saved, true)
                await loadShift()
              }}
              disabled={terminalBlocked}
            >
              Save Terminal Settings
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              onClick={loadShift}
            >
              Refresh Shift
            </button>
          </div>
        </div>

        <div className="content-card">
          <h3>Checkout Settings</h3>

          <label style={{ marginTop: '12px', display: 'block' }}>Warehouse</label>
          <select
            value={selectedWarehouse}
            onChange={(e) => setSelectedWarehouse(e.target.value)}
            disabled={terminalBlocked || !shift}
          >
            <option value="">Select warehouse</option>
            {warehouses.map((warehouse) => (
              <option key={warehouse.id} value={warehouse.id}>
                {warehouse.name}
              </option>
            ))}
          </select>

          <label style={{ marginTop: '12px', display: 'block' }}>Payment Method</label>
          <select
            value={paymentMethod}
            onChange={(e) => setPaymentMethod(e.target.value)}
            disabled={terminalBlocked || !shift}
          >
            <option value="cash">Cash</option>
            <option value="card">Card</option>
            <option value="ecocash">EcoCash</option>
            <option value="bank">Bank Transfer</option>
          </select>

          <div style={{ display: 'flex', gap: '10px', marginTop: '16px', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleCheckout}
              disabled={checkingOut || terminalBlocked || !shift}
            >
              {checkingOut ? 'Processing...' : 'Complete Sale'}
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleSyncOfflineSales}
              disabled={syncing || terminalBlocked || !shift}
            >
              {syncing ? 'Syncing...' : 'Sync Offline Sales'}
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              onClick={handlePrintLastReceipt}
            >
              Print Last Receipt
            </button>

            <button
              type="button"
              className="btn btn-danger"
              onClick={clearCart}
              disabled={terminalBlocked || !shift}
            >
              Clear Cart
            </button>
          </div>
        </div>
      </div>

      <ThermalPrinterPanel />

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Cart</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>SKU</th>
                <th>Unit Price</th>
                <th>Tax</th>
                <th>Qty</th>
                <th>Subtotal</th>
                <th>Tax Amount</th>
                <th>Line Total</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {cart.map((item) => (
                <tr key={item.product}>
                  <td>{item.product_name}</td>
                  <td>{item.product_sku}</td>
                  <td>£{formatMoney(item.unit_price)}</td>
                  <td>{formatMoney(item.tax_rate_percent)}%</td>
                  <td>
                    <input
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => updateCartQuantity(item.product, e.target.value)}
                      style={{ width: '80px' }}
                      disabled={terminalBlocked || !shift}
                    />
                  </td>
                  <td>£{formatMoney(calculateLineSubtotal(item))}</td>
                  <td>£{formatMoney(calculateLineTax(item))}</td>
                  <td>£{formatMoney(calculateLineTotal(item))}</td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-danger"
                      onClick={() => removeFromCart(item.product)}
                      disabled={terminalBlocked || !shift}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
              {cart.length === 0 ? (
                <tr><td colSpan="9">Cart is empty.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <div style={{ marginTop: '16px', display: 'grid', gap: '8px', maxWidth: '360px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Subtotal</span>
            <strong>£{formatMoney(cartSubtotal)}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Tax</span>
            <strong>£{formatMoney(cartTax)}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '18px' }}>
            <span>Total</span>
            <strong>£{formatMoney(cartGrandTotal)}</strong>
          </div>
        </div>
      </div>

      {lastReceipt ? (
        <div className="content-card" style={{ marginTop: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div>
              <h3>Last Receipt</h3>
              <p className="muted-text">{lastReceipt.is_offline ? 'Saved offline' : 'Completed online'}</p>
            </div>

            <button type="button" className="btn btn-primary" onClick={handlePrintLastReceipt}>
              Print Receipt
            </button>
          </div>

          <div className="table-wrap" style={{ marginTop: '12px' }}>
            <table>
              <tbody>
                <tr><th>Receipt Number</th><td>{lastReceipt.receipt_number}</td></tr>
                <tr><th>Date</th><td>{lastReceipt.created_at}</td></tr>
                <tr><th>Warehouse</th><td>{lastReceipt.warehouse_name}</td></tr>
                <tr><th>Terminal</th><td>{lastReceipt.terminal_name}</td></tr>
                <tr><th>Shift ID</th><td>{lastReceipt.shift_id || '-'}</td></tr>
                <tr><th>Payment Method</th><td>{lastReceipt.payment_method}</td></tr>
                <tr><th>Subtotal</th><td>£{formatMoney(lastReceipt.subtotal || lastReceipt.subtotal_amount)}</td></tr>
                <tr><th>Tax</th><td>£{formatMoney(lastReceipt.tax_total || lastReceipt.tax_amount)}</td></tr>
                <tr><th>Total</th><td>£{formatMoney(lastReceipt.grand_total || lastReceipt.total_amount)}</td></tr>
              </tbody>
            </table>
          </div>

          {Array.isArray(lastReceipt.items) && lastReceipt.items.length > 0 ? (
            <div className="table-wrap" style={{ marginTop: '12px' }}>
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Qty</th>
                    <th>Unit Price</th>
                    <th>Tax</th>
                    <th>Line Total</th>
                  </tr>
                </thead>
                <tbody>
                  {lastReceipt.items.map((item, index) => (
                    <tr key={`${item.product_name}-${index}`}>
                      <td>{item.product_name || item.name || '-'}</td>
                      <td>{item.quantity || 0}</td>
                      <td>£{formatMoney(item.unit_price)}</td>
                      <td>£{formatMoney(item.tax_amount)}</td>
                      <td>£{formatMoney(item.line_total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}

          <ReceiptPrintActions sale={lastReceipt} />
        </div>
      ) : null}

      <div className="content-card" style={{ marginTop: '20px' }}>
        <h3>Products</h3>

        <div className="table-wrap" style={{ marginTop: '12px' }}>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>SKU</th>
                <th>Selling Price</th>
                <th>Tax</th>
                <th>Rate</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id}>
                  <td>{product.name}</td>
                  <td>{product.sku}</td>
                  <td>£{formatMoney(product.selling_price)}</td>
                  <td>{product.tax_rate_name || 'No tax'}</td>
                  <td>{formatMoney(getProductTaxRatePercent(product))}%</td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => addToCart(product)}
                      disabled={terminalBlocked || !shift}
                    >
                      Add to Cart
                    </button>
                  </td>
                </tr>
              ))}
              {products.length === 0 ? (
                <tr><td colSpan="6">No products found.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
