const STORAGE_KEY = 'hute_terminal_settings'

const DEFAULT_SETTINGS = {
  terminal_id: '',
  terminal_name: 'POS Terminal 1',
  print_mode: 'browser',
  auto_print: true,
}

function generateTerminalId() {
  return `TERM-${Date.now()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`
}

export function getTerminalSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : {}

    const settings = {
      ...DEFAULT_SETTINGS,
      ...(parsed || {}),
    }

    if (!settings.terminal_id) {
      settings.terminal_id = generateTerminalId()
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    }

    return settings
  } catch {
    const fallback = {
      ...DEFAULT_SETTINGS,
      terminal_id: generateTerminalId(),
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(fallback))
    return fallback
  }
}

export function saveTerminalSettings(nextSettings) {
  const current = getTerminalSettings()
  const merged = {
    ...current,
    ...(nextSettings || {}),
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(merged))
  return merged
}