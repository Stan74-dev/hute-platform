function money(value) {
  const num = Number(value || 0)
  if (Number.isNaN(num)) return '0.00'
  return num.toFixed(2)
}

function renderReceiptHtml(receipt) {
  const items = Array.isArray(receipt?.items) ? receipt.items : []

  const itemRows = items
    .map((item) => {
      const name = item.product_name || item.name || 'Item'
      const qty = Number(item.quantity || 0)
      const unitPrice = money(item.unit_price)
      const lineTotal = money(item.line_total)

      return `
        <tr>
          <td style="padding:4px 0;">${name}</td>
          <td style="padding:4px 0; text-align:center;">${qty}</td>
          <td style="padding:4px 0; text-align:right;">£${unitPrice}</td>
          <td style="padding:4px 0; text-align:right;">£${lineTotal}</td>
        </tr>
      `
    })
    .join('')

  const subtotal = money(receipt?.subtotal ?? receipt?.total_amount ?? 0)
  const taxTotal = money(receipt?.tax_total ?? 0)
  const grandTotal = money(receipt?.grand_total ?? receipt?.total_amount ?? 0)

  return `
    <!DOCTYPE html>
    <html>
      <head>
        <title>Receipt ${receipt?.receipt_number || ''}</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            width: 300px;
            margin: 0 auto;
            padding: 12px;
            color: #000;
          }
          h2, p {
            margin: 0;
          }
          .center {
            text-align: center;
          }
          .muted {
            font-size: 12px;
            color: #333;
          }
          .line {
            border-top: 1px dashed #000;
            margin: 8px 0;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
          }
          .totals {
            margin-top: 8px;
            font-size: 13px;
          }
          .totals-row {
            display: flex;
            justify-content: space-between;
            margin: 4px 0;
          }
          .total-strong {
            font-weight: bold;
            font-size: 14px;
          }
        </style>
      </head>
      <body>
        <div class="center">
          <h2>${receipt?.business_name || 'HUTE POS'}</h2>
          <p class="muted">Receipt</p>
        </div>

        <div class="line"></div>

        <p><strong>Receipt:</strong> ${receipt?.receipt_number || '-'}</p>
        <p><strong>Date:</strong> ${receipt?.created_at || '-'}</p>
        <p><strong>Warehouse:</strong> ${receipt?.warehouse_name || '-'}</p>
        <p><strong>Terminal:</strong> ${receipt?.terminal_name || '-'}</p>
        <p><strong>Shift:</strong> ${receipt?.shift_id || '-'}</p>
        <p><strong>Cashier:</strong> ${receipt?.cashier_username || '-'}</p>
        <p><strong>Payment:</strong> ${receipt?.payment_method || '-'}</p>

        <div class="line"></div>

        <table>
          <thead>
            <tr>
              <th style="text-align:left;">Item</th>
              <th style="text-align:center;">Qty</th>
              <th style="text-align:right;">Price</th>
              <th style="text-align:right;">Total</th>
            </tr>
          </thead>
          <tbody>
            ${itemRows}
          </tbody>
        </table>

        <div class="line"></div>

        <div class="totals">
          <div class="totals-row">
            <span>Subtotal</span>
            <span>£${subtotal}</span>
          </div>
          <div class="totals-row">
            <span>Tax</span>
            <span>£${taxTotal}</span>
          </div>
          <div class="totals-row total-strong">
            <span>Total</span>
            <span>£${grandTotal}</span>
          </div>
        </div>

        <div class="line"></div>

        <p class="center muted">Thank you</p>
      </body>
    </html>
  `
}

export function printReceipt(receipt) {
  const printWindow = window.open('', '_blank', 'width=420,height=700')

  if (!printWindow) {
    throw new Error('Popup blocked. Allow popups to print receipts.')
  }

  printWindow.document.open()
  printWindow.document.write(renderReceiptHtml(receipt))
  printWindow.document.close()

  printWindow.focus()
  printWindow.onload = () => {
    printWindow.print()
  }
}