import { useState } from 'react'
import PredictionCard from './PredictionCard'
import HistoryChart from './HistoryChart'
import HistoryTable from './HistoryTable'
import './Dashboard.css'

// ── Actual historical data ────────────────────────────────────────────────────
// Will be replaced by GET /history API call once backend is ready.
// Missing cells (Mar/May 2024, Feb 2025, Feb 2026) will be filled when the user
// provides the data.
const HISTORY_2024 = [
  { period: 'Feb 2024', month: 'February',
    generation: 155,  export: 792,  import: 69,  creditableExport: 723,  totalCash: 26751.00, cash: 25414.40,
    mergeGroup: 'Feb–Mar', excludeTraining: true,  note: 'Partial month (26–29 Feb); export/import/cash are combined total for Feb+Mar' },
  { period: 'Mar 2024', month: 'March',
    generation: 782,  export: null, import: null, creditableExport: null, totalCash: null,     cash: null,
    mergeGroup: 'Feb–Mar', excludeTraining: false, note: 'Export/import/cash recorded together with February' },
  { period: 'Apr 2024', month: 'April',
    generation: 717,  export: 1230, import: 108, creditableExport: 1122, totalCash: 41514.00, cash: 41514.00,
    mergeGroup: 'Apr–May', excludeTraining: false, note: 'Export/import/cash are combined total for Apr+May' },
  { period: 'May 2024', month: 'May',
    generation: 560,  export: null, import: null, creditableExport: null, totalCash: null,     cash: null,
    mergeGroup: 'Apr–May', excludeTraining: false, note: 'Export/import/cash recorded together with April' },
  { period: 'Jun 2024', month: 'June',
    generation: 580,  export: 501,  import: 63,  creditableExport: 438,  totalCash: 16206.00, cash: 16206.00 },
  { period: 'Jul 2024', month: 'July',
    generation: 595,  export: 556,  import: 50,  creditableExport: 506,  totalCash: 18722.00, cash: 18722.00 },
  { period: 'Aug 2024', month: 'August',
    generation: 590,  export: 593,  import: 62,  creditableExport: 531,  totalCash: 19647.00, cash: 19647.00 },
  { period: 'Sep 2024', month: 'September',
    generation: 600,  export: 492,  import: 51,  creditableExport: 441,  totalCash: 16317.00, cash: 16317.00 },
  { period: 'Oct 2024', month: 'October',
    generation: 593,  export: 554,  import: 65,  creditableExport: 489,  totalCash: 18093.00, cash: 18093.00 },
  { period: 'Nov 2024', month: 'November',
    generation: 475,  export: 539,  import: 64,  creditableExport: 475,  totalCash: 17575.00, cash: 17472.44 },
  { period: 'Dec 2024', month: 'December',
    generation: 518,  export: 350,  import: 52,  creditableExport: 298,  totalCash: 11026.00, cash: 10923.44 },
]

const HISTORY_2025 = [
  { period: 'Jan 2025', month: 'January',
    generation: 446,  export: 1134, import: 126, creditableExport: 1008, totalCash: 37296.00, cash: 37296.00,
    mergeGroup: 'Jan–Feb', excludeTraining: false, note: 'Export/import/cash are combined total for Jan+Feb' },
  { period: 'Feb 2025', month: 'February',
    generation: 670,  export: null, import: null, creditableExport: null, totalCash: null,     cash: null,
    mergeGroup: 'Jan–Feb', excludeTraining: false, note: 'Export/import/cash recorded together with January' },
  { period: 'Mar 2025', month: 'March',
    generation: 690,  export: 617,  import: 65,  creditableExport: 552,  totalCash: 20424.00, cash: 20424.00 },
  { period: 'Apr 2025', month: 'April',
    generation: 675,  export: 664,  import: 66,  creditableExport: 598,  totalCash: 22126.00, cash: 22126.00 },
  { period: 'May 2025', month: 'May',
    generation: 612,  export: 553,  import: 58,  creditableExport: 495,  totalCash: 18315.00, cash: 18315.00 },
  { period: 'Jun 2025', month: 'June',
    generation: 608,  export: 509,  import: 51,  creditableExport: 458,  totalCash: 16946.00, cash: 16946.00 },
  { period: 'Jul 2025', month: 'July',
    generation: 622,  export: 569,  import: 60,  creditableExport: 509,  totalCash: 18833.00, cash: 18833.00 },
  { period: 'Aug 2025', month: 'August',
    generation: 634,  export: 634,  import: 65,  creditableExport: 569,  totalCash: 21053.00, cash: 20970.95 },
  { period: 'Sep 2025', month: 'September',
    generation: 568,  export: 536,  import: 65,  creditableExport: 471,  totalCash: 17427.00, cash: 17344.95 },
  { period: 'Oct 2025', month: 'October',
    generation: 567,  export: 361,  import: 42,  creditableExport: 319,  totalCash: 11803.00, cash: 11720.95 },
  { period: 'Nov 2025', month: 'November',
    generation: 437,  export: 436,  import: 55,  creditableExport: 381,  totalCash: 14097.00, cash: 14014.95 },
  { period: 'Dec 2025', month: 'December',
    generation: 506,  export: 408,  import: 66,  creditableExport: 342,  totalCash: 12654.00, cash: 12572.00 },
]

const HISTORY_2026 = [
  { period: 'Jan 2026', month: 'January',
    generation: 512,  export: 953,  import: 120, creditableExport: 833,  totalCash: 30821.00, cash: 30631.90,
    mergeGroup: 'Jan–Feb', excludeTraining: false, note: 'Export/import/cash are combined total for Jan+Feb' },
  { period: 'Feb 2026', month: 'February',
    generation: 518,  export: null, import: null, creditableExport: null, totalCash: null,     cash: null,
    mergeGroup: 'Jan–Feb', excludeTraining: false, note: 'Export/import/cash recorded together with January' },
  { period: 'Mar 2026', month: 'March',
    generation: 816,  export: 608,  import: 65,  creditableExport: 543,  totalCash: 20091.00, cash: null,
    note: 'Cash not yet received (expected April 20–28, 2026)' },
]

const HISTORY_BY_YEAR = [
  { year: 2024, rows: HISTORY_2024 },
  { year: 2025, rows: HISTORY_2025 },
  { year: 2026, rows: HISTORY_2026 },
]

// Chart uses only rows where generation is known
const CHART_DATA = [...HISTORY_2024, ...HISTORY_2025, ...HISTORY_2026]
  .filter(r => r.generation !== null)

// ── Mock predictions (placeholder until model is trained) ─────────────────────
// Values are estimates — will be replaced by POST /predict API response.
// Predictions start from April 2026 — the current predictive month.
// Even though today is April 2026, April is still predictive because:
// (a) the CEB delegate hasn't visited yet this month, and
// (b) March 2026's cash hasn't been received yet (expected April 20–28).
// Will be replaced by POST /predict API response once the model is trained.
const MOCK_PREDICTIONS = [
  { month: 'Apr 2026',  generation: { v: 650, lo: 585, hi: 715 }, creditableExport: { v: 555, lo: 495, hi: 615 }, cash: { v: 20535.00, lo: 18315.00, hi: 22755.00 } },
  { month: 'May 2026',  generation: { v: 580, lo: 520, hi: 640 }, creditableExport: { v: 510, lo: 450, hi: 570 }, cash: { v: 18870.00, lo: 16650.00, hi: 21090.00 } },
  { month: 'Jun 2026',  generation: { v: 560, lo: 500, hi: 620 }, creditableExport: { v: 488, lo: 428, hi: 548 }, cash: { v: 18056.00, lo: 15836.00, hi: 20276.00 } },
  { month: 'Jul 2026',  generation: { v: 600, lo: 540, hi: 660 }, creditableExport: { v: 520, lo: 460, hi: 580 }, cash: { v: 19240.00, lo: 17020.00, hi: 21460.00 } },
  { month: 'Aug 2026',  generation: { v: 620, lo: 558, hi: 682 }, creditableExport: { v: 552, lo: 490, hi: 614 }, cash: { v: 20424.00, lo: 18130.00, hi: 22718.00 } },
  { month: 'Sep 2026',  generation: { v: 575, lo: 515, hi: 635 }, creditableExport: { v: 460, lo: 400, hi: 520 }, cash: { v: 17020.00, lo: 14800.00, hi: 19240.00 } },
  { month: 'Oct 2026',  generation: { v: 570, lo: 510, hi: 630 }, creditableExport: { v: 380, lo: 320, hi: 440 }, cash: { v: 14060.00, lo: 11840.00, hi: 16280.00 } },
  { month: 'Nov 2026',  generation: { v: 450, lo: 395, hi: 505 }, creditableExport: { v: 390, lo: 335, hi: 445 }, cash: { v: 14430.00, lo: 12395.00, hi: 16465.00 } },
  { month: 'Dec 2026',  generation: { v: 510, lo: 450, hi: 570 }, creditableExport: { v: 340, lo: 280, hi: 400 }, cash: { v: 12580.00, lo: 10360.00, hi: 14800.00 } },
  { month: 'Jan 2027',  generation: { v: 480, lo: 420, hi: 540 }, creditableExport: { v: 920, lo: 860, hi: 980 }, cash: { v: 34040.00, lo: 31820.00, hi: 36260.00 } },
  { month: 'Feb 2027',  generation: { v: 640, lo: 576, hi: 704 }, creditableExport: { v: 570, lo: 506, hi: 634 }, cash: { v: 21090.00, lo: 18722.00, hi: 23458.00 } },
  { month: 'Mar 2027',  generation: { v: 760, lo: 684, hi: 836 }, creditableExport: { v: 590, lo: 526, hi: 654 }, cash: { v: 21830.00, lo: 19462.00, hi: 24198.00 } },
]

const PERIOD_OPTIONS = [
  { label: 'Next 1 Month',  value: 1 },
  { label: 'Next 3 Months', value: 3 },
  { label: 'Next 6 Months', value: 6 },
  { label: 'Next 1 Year',   value: 12 },
]

// ── Component ─────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [period, setPeriod]           = useState(1)
  const [modelStatus, setModelStatus] = useState('untrained') // untrained | training | ready

  const predictions = MOCK_PREDICTIONS.slice(0, period)

  function handleTrain() {
    setModelStatus('training')
    // TODO: call POST /train API
    setTimeout(() => setModelStatus('ready'), 2000)
  }

  const statusBadge = {
    untrained: <span className="badge badge-pending">Model not trained</span>,
    training:  <span className="badge badge-training">Training…</span>,
    ready:     <span className="badge badge-ready">Model ready</span>,
  }[modelStatus]

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
          <button
            className="train-btn"
            onClick={handleTrain}
            disabled={modelStatus === 'training'}
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
            <p className="section-subtitle">
              {period === 1
                ? `${predictions[0].month} — includes confidence range`
                : `${predictions[0].month} → ${predictions[period - 1].month} — includes confidence range`}
            </p>
          </div>
        </div>
        <div className="cards-row" id="prediction-cards">
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
          <HistoryChart data={CHART_DATA} />
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
        {HISTORY_BY_YEAR.map(({ year, rows }) => (
          <HistoryTable key={year} year={year} rows={rows} />
        ))}
      </section>

    </div>
  )
}
