/**
 * API service layer — all calls to the FastAPI backend go through here.
 * Vite proxies /api/* → http://localhost:8000/* (see vite.config.js).
 */

const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail?.detail ?? `Request failed: ${res.status}`)
  }
  return res.json()
}

/** Returns { years: [{ year, rows: [...] }] } */
export function fetchHistory() {
  return request('/history')
}

/**
 * Returns { modelTrained, predictions: [...] }
 * @param {number} months - 1, 3, 6, or 12
 */
export function fetchPredictions(months = 1) {
  return request(`/predict?months=${months}`)
}

/** Triggers model training. Returns { status, trainingRecords, testRecords, trainPeriod, testPeriod } */
export function trainModel() {
  return request('/train', { method: 'POST' })
}

/** Returns { modelTrained: boolean } */
export function fetchStatus() {
  return request('/status')
}
