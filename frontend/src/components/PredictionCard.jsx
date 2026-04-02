import './PredictionCard.css'

function formatValue(value, unit) {
  if (value === null || value === undefined) return '—'
  if (unit === 'LKR') {
    return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }
  return value.toLocaleString()
}

export default function PredictionCard({ label, icon, unit, color, predictions }) {
  if (!predictions || predictions.length === 0) return null

  const single = predictions.length === 1
  const first  = predictions[0]

  // Confidence expressed as ±% half-width relative to the point estimate
  const confidencePct = first.value > 0
    ? Math.round(((first.upper - first.lower) / 2 / first.value) * 100)
    : 0

  return (
    <div className="prediction-card" style={{ '--card-color': color }}>
      <div className="card-accent" />
      <div className="card-header">
        <span className="card-icon">{icon}</span>
        <span className="card-label">{label}</span>
      </div>

      {single ? (
        <div className="card-single">
          <div className="single-month">{first.month}</div>
          <div className="card-value">
            <span className="value-number">{formatValue(first.value, unit)}</span>
            <span className="value-unit">{unit}</span>
          </div>
          <div className="card-range">
            <span className="range-label">90% range</span>
            <span className="range-bound range-lo">↓ {formatValue(first.lower, unit)}</span>
            <span className="range-sep">–</span>
            <span className="range-bound range-hi">↑ {formatValue(first.upper, unit)}</span>
            <span className="confidence-pct">±{confidencePct}%</span>
          </div>
        </div>
      ) : (
        <div className="card-multi">
          <div className="multi-header">
            <span>Month</span>
            <span>Value</span>
            <span>Range</span>
          </div>
          <div className="multi-rows">
            {predictions.map((p) => (
              <div key={p.month} className="multi-row">
                <span className="multi-month">{p.month}</span>
                <span className="multi-value">
                  {formatValue(p.value, unit)}
                  <span className="multi-unit"> {unit}</span>
                </span>
                <span className="multi-range">
                  <span className="range-hi-sm">↑ {formatValue(p.upper, unit)}</span>
                  <span className="range-lo-sm">↓ {formatValue(p.lower, unit)}</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
