/**
 * API service layer — all calls to the FastAPI backend go through here.
 * Vite proxies /api/* → http://localhost:8000/* (see vite.config.js).
 *
 * Demo mode (VITE_DEMO_MODE=true at build time) is for the public GitHub
 * Pages site, which has no backend. The same functions then read JSON files
 * generated at build time from synthetic data (backend/scripts/export_demo_data.py).
 */

export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true'

const BASE = DEMO_MODE ? `${import.meta.env.BASE_URL}demo` : '/api'

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
  return request(DEMO_MODE ? '/history.json' : '/history')
}

/**
 * Returns { modelTrained, predictions: [...] }
 * @param {number} months - 1, 3, 6, or 12
 */
export async function fetchPredictions(months = 1) {
  if (DEMO_MODE) {
    // The demo file holds 12 months; show as many as were asked for.
    const all = await request('/predictions.json')
    return { ...all, predictions: all.predictions.slice(0, months) }
  }
  return request(`/predict?months=${months}`)
}

/** Triggers model training. Returns { status, trainingRecords, testRecords, trainPeriod, testPeriod } */
export function trainModel() {
  if (DEMO_MODE) {
    return Promise.reject(new Error('Training is switched off in the demo.'))
  }
  return request('/train', { method: 'POST' })
}

/** Returns { modelTrained: boolean } */
export function fetchStatus() {
  return request(DEMO_MODE ? '/status.json' : '/status')
}
