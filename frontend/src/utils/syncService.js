import API from '../api/client'
import {
  getUnsyncedSales,
  markSaleSynced,
  incrementFailedAttempt,
  clearSyncedSales,
} from './offlineSales'

function isNetworkError(err) {
  return !err.response
}

export async function syncOfflineSales() {
  const unsyncedSales = getUnsyncedSales()

  if (!unsyncedSales.length) {
    return {
      synced: 0,
      failed: 0,
      total: 0,
    }
  }

  let synced = 0
  let failed = 0

  for (const sale of unsyncedSales) {
    try {
      await API.post('/sales/checkout/', {
        warehouse: sale.payload.warehouse,
        payment_method: sale.payload.payment_method,
        terminal: sale.payload.terminal,
        items: (sale.payload.items || []).map((item) => ({
          product: item.product,
          quantity: item.quantity,
        })),
      })

      markSaleSynced(sale.offline_id)
      synced += 1
    } catch (error) {
      incrementFailedAttempt(sale.offline_id)
      failed += 1

      if (!isNetworkError(error)) {
        throw new Error(error.response?.data?.detail || 'Backend rejected offline sync.')
      }
    }
  }

  clearSyncedSales()

  return {
    synced,
    failed,
    total: unsyncedSales.length,
  }
}