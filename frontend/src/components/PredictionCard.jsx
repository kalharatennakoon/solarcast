import './PredictionCard.css'

export default function PredictionCard({ label, value, unit, lower, upper, color, icon }) {
  return (
    <div className="prediction-card" style={{ '--card-color': color }}>
      <div className="card-icon">{icon}</div>
      <div className="card-label">{label}</div>
      <div className="card-value">
        <span className="value-number">{value.toLocaleString()}</span>
        <span className="value-unit">{unit}</span>
      </div>
      {lower != null && upper != null && (
        <div className="card-range">
          {lower.toLocaleString()} – {upper.toLocaleString()} {unit}
        </div>
      )}
      <div className="card-accent" />
    </div>
  )
}
