// Tiny fetch wrapper + shared formatting helpers. URLs are relative ("/api/..."),
// proxied to FastAPI in dev and served same-origin in production.

const JSON_HEADERS = { 'Content-Type': 'application/json' }

async function req(method, url, body) {
  const opts = { method }
  if (body !== undefined) {
    opts.headers = JSON_HEADERS
    opts.body = JSON.stringify(body)
  }
  const res = await fetch(url, opts)
  if (!res.ok) throw new Error(`${method} ${url} → ${res.status}`)
  const text = await res.text()
  return text ? JSON.parse(text) : null
}

export const api = {
  get: (u) => req('GET', u),
  post: (u, b) => req('POST', u, b),
  put: (u, b) => req('PUT', u, b),
  del: (u) => req('DELETE', u),
}

// --- formatting ---
export const money = (n) => (n < 0 ? '-' : '') + '$' + Math.abs(n).toFixed(2)
export const dollars = (n) =>
  (n >= 0 ? '+' : '-') + '$' + Math.abs(Math.round(n)).toLocaleString('en-US')
export const usd = (n) => '$' + Math.round(n).toLocaleString('en-US')
export const meta = (spent, limit) => `${usd(spent)} / ${usd(limit)}`

// Gauge status from percent used: <70 green, 70–100 amber, >=100 red.
export const statusFromPct = (pct) => (pct >= 100 ? 'over' : pct >= 70 ? 'warn' : 'ok')

export const weekLabel = (w, current) => (w === current ? 'This week' : 'Week ' + w)

// "2026-06" -> "June 2026"
export function monthLabel(key) {
  if (!key) return ''
  const [y, m] = key.split('-').map(Number)
  return new Date(y, m - 1, 1).toLocaleString('en-US', { month: 'long', year: 'numeric' })
}

// Default selected week: always the current week ("This week") when known,
// even if it has no entries yet; falls back to the latest week, else 'all'.
export function defaultWeek(weeks, current) {
  if (current != null) return current
  return weeks.length ? Math.max(...weeks) : 'all'
}
