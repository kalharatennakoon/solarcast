import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import './HistoryChart.css'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} style={{ color: entry.color }}>
          {entry.name}: <strong>{entry.value.toLocaleString()}</strong> kWh
        </p>
      ))}
    </div>
  )
}

export default function HistoryChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">
        No historical data available yet.
      </div>
    )
  }

  return (
    <div className="chart-wrapper">
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data} margin={{ top: 8, right: 24, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="period"
            tick={{ fontSize: 12, fill: '#64748b' }}
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#64748b' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${v}`}
            unit=" kWh"
            width={75}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: '13px', paddingTop: '16px' }}
          />
          <Line
            type="monotone"
            dataKey="generation"
            name="Generation"
            stroke="#f59e0b"
            strokeWidth={2.5}
            dot={{ r: 3, fill: '#f59e0b' }}
            activeDot={{ r: 5 }}
          />
          <Line
            type="monotone"
            dataKey="creditableExport"
            name="Creditable Export"
            stroke="#3b82f6"
            strokeWidth={2.5}
            dot={{ r: 3, fill: '#3b82f6' }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
