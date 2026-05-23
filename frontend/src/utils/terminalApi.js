import API from '../api/client'

export async function registerTerminalWithBackend(settings) {
  const payload = {
    terminal_id: settings.terminal_id,
    terminal_name: settings.terminal_name,
    preferred_print_mode: settings.print_mode,
    auto_print: settings.auto_print,
  }

  const { data } = await API.post('/accounts/terminals/register/', payload)
  return data
}