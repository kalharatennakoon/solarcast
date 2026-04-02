import { useState, useEffect } from 'react'
import PredictionCard from './PredictionCard'
import HistoryChart from './HistoryChart'
import HistoryTable from './HistoryTable'
import { fetchHistory, fetchPredictions, fetchStatus, trainModel } from '../api'
import './Dashboard.css'


function formatTrainedAt(isoString) {
  const d = new Date(isoString)
  return d.toLocaleString(undefined, {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

const PERIOD_OPTIONS = [
  { label: 'Next 1 Month',  value: 1 },
  { label: 'Next 3 Months', value: 3 },
  { label: 'Next 6 Months', value: 6 },
  { label: 'Next 1 Year',   value: 12 },
]

// ── Component ─────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [period, setPeriod]             = useState(1)
  const [modelStatus, setModelStatus]   = useState('untrained')
  const [lastTrainedAt, setLastTrainedAt] = useState(null)
  const [predictions, setPredictions]   = useState([])
  const [historyByYear, setHistoryByYear] = useState([])
  const [chartData, setChartData]       = useState([])
  const [backendUp, setBackendUp]       = useState(false)
  const [loadingHistory, setLoadingHistory]     = useState(true)
  const [loadingPredictions, setLoadingPredictions] = useState(false)

  // On mount: check model status and load history
  useEffect(() => {
    fetchStatus()
      .then(({ modelTrained, lastTrainedAt }) => {
        setBackendUp(true)
        setModelStatus(modelTrained ? 'ready' : 'untrained')
        setLastTrainedAt(lastTrainedAt ?? null)
      })
      .catch(() => {
        setBackendUp(false)
        setModelStatus('error')
      })

    fetchHistory()
      .then(({ years }) => {
        const byYear = years.map(({ year, rows }) => ({
          year,
          rows: rows.map(r => ({
            period: r.period,
            month: r.month,
            generation: r.generation,
            export: r.export,
            import: r.importKwh,
            creditableExport: r.creditableExport,
            totalCash: r.totalCash,
            cash: r.cashReceived,
            mergeGroup: r.mergeGroup,
            excludeTraining: r.excludeTraining,
            note: r.note,
          })),
        }))
        setHistoryByYear(byYear)
        setChartData(byYear.flatMap(y => y.rows).filter(r => r.generation !== null))
      })
      .finally(() => setLoadingHistory(false))
  }, [])

  // Re-fetch predictions when period or model status changes
  useEffect(() => {
    if (!backendUp || modelStatus !== 'ready') {
      setPredictions([])
      return
    }
    setPredictions([])
    setLoadingPredictions(true)
    fetchPredictions(period)
      .then(({ predictions: preds }) => {
        setPredictions(preds.map(p => ({
          month: p.month,
          generation:       { v: p.generation.value,       lo: p.generation.lower,       hi: p.generation.upper },
          creditableExport: { v: p.creditableExport.value, lo: p.creditableExport.lower, hi: p.creditableExport.upper },
          cash:             { v: p.cash.value,             lo: p.cash.lower,             hi: p.cash.upper },
        })))
      })
      .catch(() => setPredictions([]))
      .finally(() => setLoadingPredictions(false))
  }, [period, modelStatus, backendUp])

  async function handleTrain() {
    setModelStatus('training')
    try {
      const result = await trainModel()
      setModelStatus('ready')
      setLastTrainedAt(result.lastTrainedAt ?? null)
    } catch {
      setModelStatus('error')
    }
  }

  const statusBadge = {
    untrained: <span className="badge badge-pending">Model not trained</span>,
    training:  <span className="badge badge-training">Training…</span>,
    ready:     <span className="badge badge-ready">Model ready</span>,
    error:     <span className="badge badge-error">Backend not running</span>,
  }[modelStatus]

  const hasPredictions = predictions.length > 0

  return (
    <div className="dashboard">

      {/* ── Controls bar ── */}
      <div className="controls-bar">
        <div className="period-selector">
          <label htmlFor="period-select">Prediction period</label>
          <select
            id="period-select"
            value={period}
            onChange={e => setPeriod(Number(e.target.value))}
          >
            {PERIOD_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
        <div className="train-area">
          {statusBadge}
          {lastTrainedAt && (
            <span className="last-trained">
              Last trained: {formatTrainedAt(lastTrainedAt)}
            </span>
          )}
          <button
            className="train-btn"
            onClick={handleTrain}
            disabled={modelStatus === 'training' || !backendUp}
          >
            {modelStatus === 'training' ? 'Training…' : 'Train Model'}
          </button>
        </div>
      </div>

      {/* ── Prediction cards ── */}
      <section className="section">
        <div className="section-header">
          <div>
            <h2 className="section-title">Predictions</h2>
            {hasPredictions && !loadingPredictions && (
              <p className="section-subtitle">
                {predictions.length === 1
                  ? `${predictions[0].month} — includes confidence range`
                  : `${predictions[0].month} → ${predictions[predictions.length - 1].month} — includes confidence range`}
              </p>
            )}
          </div>
        </div>

        {loadingPredictions && (
          <div className="state-message">Fetching predictions…</div>
        )}

        {!loadingPredictions && !hasPredictions && (
          <div className="state-message">
            {modelStatus === 'error'
              ? 'Backend is not running. Start the backend server and refresh.'
              : 'Train the model to see predictions.'}
          </div>
        )}

        {!loadingPredictions && hasPredictions && (
          <>
            <div className="cards-row">
              <PredictionCard
                label="Solar Generation"
                icon="⚡"
                unit="kWh"
                color="var(--color-generation)"
                predictions={predictions.map(p => ({
                  month: p.month,
                  value: p.generation.v,
                  lower: p.generation.lo,
                  upper: p.generation.hi,
                }))}
              />
              <PredictionCard
                label="Creditable Export"
                icon="🔌"
                unit="kWh"
                color="var(--color-export)"
                predictions={predictions.map(p => ({
                  month: p.month,
                  value: p.creditableExport.v,
                  lower: p.creditableExport.lo,
                  upper: p.creditableExport.hi,
                }))}
              />
              <PredictionCard
                label="Expected Cash"
                icon="💰"
                unit="LKR"
                color="var(--color-cash)"
                predictions={predictions.map(p => ({
                  month: p.month,
                  value: p.cash.v,
                  lower: p.cash.lo,
                  upper: p.cash.hi,
                }))}
              />
            </div>
            <p className="cards-hint">
              The model is 90% confident the real outcome will land within that range. The ±% shows how wide the range is — a smaller ±% means a tighter, more precise prediction.
            </p>
          </>
        )}
      </section>

      {/* ── Historical chart ── */}
      <section className="section">
        <div className="section-header">
          <div>
            <h2 className="section-title">Historical Performance</h2>
            <p className="section-subtitle">Monthly generation and creditable export (kWh) — scroll to see full history</p>
          </div>
        </div>
        <div className="chart-card">
          {loadingHistory
            ? <div className="state-message">Loading history…</div>
            : <HistoryChart data={chartData} />}
        </div>
      </section>

      {/* ── Historical data tables ── */}
      <section className="section">
        <div className="section-header">
          <div>
            <h2 className="section-title">Historical Data</h2>
            <p className="section-subtitle">Raw records by year — expand to view</p>
          </div>
        </div>
        {loadingHistory
          ? <div className="state-message">Loading records…</div>
          : historyByYear.map(({ year, rows }) => (
              <HistoryTable key={year} year={year} rows={rows} />
            ))}
      </section>

    </div>
  )
}
