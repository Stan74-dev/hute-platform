const STORAGE_KEY = 'hute_offline_sales_queue'

export function getOfflineSales() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function saveOfflineSale(payload) {
  const sales = getOfflineSales()

  const offlineSale = {
    offline_id: `OFF-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    synced: false,
    failed_attempts: 0,
    created_at: new Date().toISOString(),
    payload,
  }

  sales.push(offlineSale)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sales))
  return offlineSale
}

export function markSaleSynced(offlineId) {
  const sales = getOfflineSales().map((sale) =>
    sale.offline_id === offlineId
      ? {
          ...sale,
          synced: true,
          synced_at: new Date().toISOString(),
        }
      : sale
  )

  localStorage.setItem(STORAGE_KEY, JSON.stringify(sales))
}

export function incrementFailedAttempt(offlineId) {
  const sales = getOfflineSales().map((sale) =>
    sale.offline_id === offlineId
      ? {
          ...sale,
          failed_attempts: Number(sale.failed_attempts || 0) + 1,
          last_failed_at: new Date().toISOString(),
        }
      : sale
  )

  localStorage.setItem(STORAGE_KEY, JSON.stringify(sales))
}

export function getUnsyncedSales() {
  return getOfflineSales().filter((sale) => !sale.synced)
}

export function clearSyncedSales() {
  const unsynced = getOfflineSales().filter((sale) => !sale.synced)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(unsynced))
}

export function clearAllOfflineSales() {
  localStorage.removeItem(STORAGE_KEY)
}

export function buildOfflineReceiptFromPayload(offlineSale, warehouseName = '') {
  const payload = offlineSale?.payload || {}
  const terminal = payload?.terminal || {}

  return {
    receipt_number: offlineSale?.offline_id || 'OFFLINE',
    created_at: offlineSale?.created_at || new Date().toISOString(),
    warehouse_name: warehouseName || '-',
    payment_method: payload.payment_method || 'cash',
    total_amount: (payload.items || []).reduce(
      (sum, item) => sum + Number(item.unit_price || 0) * Number(item.quantity || 0),
      0
    ),
    is_offline: true,
    terminal_name: terminal.terminal_name || '',
    terminal_id: terminal.terminal_id || '',
    items: (payload.items || []).map((item) => ({
      product_name: item.product_name || `Product ${item.product}`,
      quantity: Number(item.quantity || 0),
      unit_price: Number(item.unit_price || 0),
    })),
  }
}