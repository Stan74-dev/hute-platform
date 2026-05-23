const BRIDGE_URL = 'http://127.0.0.1:8765'

export async function checkLocalPrinterBridge() {
  const response = await fetch(`${BRIDGE_URL}/health`)
  if (!response.ok) {
    throw new Error('Print bridge unavailable')
  }
  return response.json()
}

export async function printReceiptViaBridge(receipt) {
  const response = await fetch(`${BRIDGE_URL}/print`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(receipt),
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(data?.detail || 'Print failed')
  }

  return data
}