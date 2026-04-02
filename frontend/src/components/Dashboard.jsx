import { useState } from 'react'
import PredictionCard from './PredictionCard'
import HistoryChart from './HistoryChart'
import './Dashboard.css'

// Placeholder data — will be replaced by API calls
const MOCK_PREDICTION = {
  month: 'May 2026',
  generation: { value: 580, lower: 520, upper: 640 },
  creditableExport: { value: 510, lower: 450, upper: 570 },
  cashReceived: { value: 18870, lower: 16650, upper: 21090 },
}

const MOCK_HISTORY = [
  { period: 'Jun 2024', generation: 580, creditableExport: 438 },
  { period: 'Jul 2024', generation: 595, creditableExport: 506 },
  { period: 'Aug 2024', generation: 590, creditableExport: 531 },
  { period: 'Sep 2024', generation: 600, creditableExport: 441 },
  { period: 'Oct 2024', generation: 593, creditableExport: 489 },
  { period: 'Nov 2024', generation: 475, creditableExport: 475 },
  { period: 'Dec 2024', generation: 518, creditableExport: 298 },
  { period: 'Jan 2025', generation: 446, creditableExport: 1008 },
  { period: 'Mar 2025', generation: 690, creditableExport: 552 },
  { period: 'Apr 2025', generation: 675, creditableExport: 598 },
  { period: 'May 2025', generation: 612, creditableExport: 495 },
  { period: 'Jun 2025', generation: 608, creditableExport: 458 },
  { period: 'Jul 2025', generation: 622, creditableExport: 509 },
  { period: 'Aug 2025', generation: 634, creditableExport: 569 },
  { period: 'Sep 2025', generation: 568, creditableExport: 471 },
  { period: 'Oct 2025', generation: 567, creditableExport: 319 },
  { period: 'Nov 2025', generation: 437, creditableExport: 381 },
  { period: 'Dec 2025', generation: 506, creditableExport: 342 },
  { period: 'Jan 2026', generation: 512, creditableExport: 833 },
  { period: 'Mar 2026', generation: 816, creditableExport: 543 },
]

export default function Dashboard() {
  const [prediction] = useState(MOCK_PREDICTION)
  const [history] = useState(MOCK_HISTORY)

  return (
    <div className="dashboard">

      <section className="section">
        <div className="section-header">
          <div>
            <h2 className="section-title">Next Month Prediction</h2>
            <p className="section-subtitle">{prediction.month} — values include confidence range</p>
          </div>
          <span className="badge badge-pending">Model not trained</span>
        </div>
        <div className="cards-row">
          <PredictionCard
            label="Solar Generation"
            value={prediction.generation.value}
            unit="kWh"
            lower={prediction.generation.lower}
            upper={prediction.generation.upper}
            color="var(--color-generation)"
            icon="⚡"
          />
          <PredictionCard
            label="Creditable Export"
            value={prediction.creditableExport.value}
            unit="kWh"
            lower={prediction.creditableExport.lower}
            upper={prediction.creditableExport.upper}
            color="var(--color-export)"
            icon="🔌"
          />
          <PredictionCard
            label="Expected Cash"
            value={prediction.cashReceived.value}
            unit="LKR"
            lower={prediction.cashReceived.lower}
            upper={prediction.cashReceived.upper}
            color="var(--color-cash)"
            icon="💰"
          />
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <div>
            <h2 className="section-title">Historical Performance</h2>
            <p className="section-subtitle">Monthly generation and creditable export (kWh)</p>
          </div>
        </div>
        <div className="chart-card">
          <HistoryChart data={history} />
        </div>
      </section>

    </div>
  )
}
