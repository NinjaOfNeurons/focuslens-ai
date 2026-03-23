const BASE = "http://localhost:8000/api"

export async function getLatestSession() {
  const r = await fetch(`${BASE}/latest-session`)
  return r.json()
}

export async function getSessionReport(sessionId) {
  const r = await fetch(`${BASE}/sessions/${sessionId}`)
  return r.json()
}

export async function getLiveFeed(sessionId) {
  const r = await fetch(`${BASE}/live/${sessionId}`)
  return r.json()
}