import qz from 'qz-tray'

let qzConnected = false

function escposInit() {
  return '\x1B\x40'
}

function escposAlignLeft() {
  return '\x1B\x61\x00'
}

function escposAlignCenter() {
  return '\x1B\x61\x01'
}

function escposBoldOn() {
  return '\x1B\x45\x01'
}

function escposBoldOff() {
  return '\x1B\x45\x00'
}

function escposDoubleOn() {
  return '\x1D\x21\x11'
}

function escposDoubleOff() {
  return '\x1D\x21\x00'
}

function escposCut() {
  return '\x1D\x56\x00'
}

function repeat(char, count) {
  return new Array(count + 1).join(char)
}

function safeMoney(value) {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0.00'
  return num.toFixed(2)
}

function padRight(text, width) {
  const value = String(text ?? '')
  if (value.length >= width) return value.slice(0, width)
  return value + repeat(' ', width - value.length)
}

function formatLineColumns(left, right, totalWidth = 32) {
  const rightText = String(right ?? '')
  const leftWidth = Math.max(0, totalWidth - rightText.length)
  return `${padRight(left, leftWidth)}${rightText}`
}

async function ensureQzConnection() {
  if (qzConnected && qz.websocket.isActive()) {
    return
  }

  qz.websocket.setErrorCallbacks((event) => {
    console.error('QZ Tray websocket error:', event)
  })

  qz.websocket.setClosedCallbacks((event) => {
    console.warn('QZ Tray websocket closed:', event)
    qzConnected = false
  })

  await qz.websocket.connect({
    retries: 1,
    delay: 0,
  })

  qzConnected = true
}

export async function disconnectQz() {
  if (qz.websocket.isActive()) {
    await qz.websocket.disconnect()
  }
  qzConnected = false
}

export async function findPrinters() {
  await ensureQzConnection()
  const printers = await qz.printers.find()

  if (Array.isArray(printers)) {
    return printers
  }

  return printers ? [printers] : []
}

export function buildReceiptLines(sale) {
  const businessName = sale?.business_name || 'HUTE POS'
  const cashier = sale?.cashier_username || '-'
  const receiptNumber = sale?.receipt_number || sale?.sale_code || `SALE-${sale?.id || ''}`
  const paymentMethod = sale?.payment_method || '-'
  const createdAt = sale?.created_at || new Date().toISOString()
  const items = Array.isArray(sale?.items) ? sale.items : []

  const subtotal = safeMoney(sale?.subtotal ?? sale?.total_amount ?? 0)
  const tax = safeMoney(sale?.tax_total ?? 0)
  const total = safeMoney(sale?.grand_total ?? sale?.total_amount ?? 0)

  const lines = []

  lines.push(escposInit())
  lines.push(escposAlignCenter())
  lines.push(escposBoldOn())
  lines.push(escposDoubleOn())
  lines.push(`${businessName}\n`)
  lines.push(escposDoubleOff())
  lines.push(escposBoldOff())
  lines.push('Receipt\n')
  lines.push(escposAlignLeft())
  lines.push(`${repeat('-', 32)}\n`)
  lines.push(`Receipt: ${receiptNumber}\n`)
  lines.push(`Cashier: ${cashier}\n`)
  lines.push(`Payment: ${paymentMethod}\n`)
  lines.push(`Date: ${createdAt}\n`)
  lines.push(`${repeat('-', 32)}\n`)

  items.forEach((item) => {
    const name = item?.name || item?.product_name || 'Item'
    const qty = Number(item?.quantity || 0)
    const lineTotal = safeMoney(item?.line_total ?? item?.total ?? 0)

    lines.push(`${name}\n`)
    lines.push(`${formatLineColumns(`x${qty}`, `£${lineTotal}`)}\n`)
  })

  lines.push(`${repeat('-', 32)}\n`)
  lines.push(`${formatLineColumns('Subtotal', `£${subtotal}`)}\n`)
  lines.push(`${formatLineColumns('Tax', `£${tax}`)}\n`)
  lines.push(escposBoldOn())
  lines.push(`${formatLineColumns('TOTAL', `£${total}`)}\n`)
  lines.push(escposBoldOff())
  lines.push(`${repeat('-', 32)}\n`)
  lines.push(escposAlignCenter())
  lines.push('Thank you\n')
  lines.push('\n\n\n')
  lines.push(escposCut())

  return lines
}

export function buildTestReceipt() {
  return {
    business_name: 'HUTE POS',
    receipt_number: 'TEST-001',
    created_at: new Date().toLocaleString(),
    payment_method: 'test',
    subtotal: 5.0,
    tax_total: 0.0,
    grand_total: 5.0,
    total_amount: 5.0,
    cashier_username: 'Test User',
    items: [
      {
        name: 'Printer Test Item',
        product_name: 'Printer Test Item',
        quantity: 1,
        unit_price: 5.0,
        line_total: 5.0,
      },
    ],
  }
}

export async function printThermalReceipt(printerName, sale) {
  if (!printerName) {
    throw new Error('Printer name is required.')
  }

  await ensureQzConnection()

  const config = qz.configs.create(printerName)

  const rawLines = buildReceiptLines(sale).map((line) => ({
    type: 'raw',
    format: 'plain',
    data: line,
  }))

  await qz.print(config, rawLines)
}

export async function printTestReceipt(printerName) {
  const sale = buildTestReceipt()
  await printThermalReceipt(printerName, sale)
}