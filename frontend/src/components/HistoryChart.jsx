import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend,
} from 'recharts'
import './HistoryChart.css'

const BAR_WIDTH = 64  // px per data point

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} style={{ color: entry.color }}>
          {entry.name}: <strong>{entry.value?.toLocaleString()}</strong> kWh
        </p>
      ))}
    </div>
  )
}

export default function HistoryChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">No historical data available yet.</div>
    )
  }

  const chartWidth = Math.max(data.length * BAR_WIDTH, 600)

  return (
    <div className="chart-scroll-container">
      <div style={{ width: chartWidth, height: 320 }}>
        <LineChart
          width={chartWidth}
          height={320}
          data={data}
          margin={{ top: 8, right: 24, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="period"
            tick={{ fontSize: 11, fill: '#64748b' }}
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
            interval={0}
            angle={-35}
            textAnchor="end"
            height={50}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#64748b' }}
            tickLine={false}
            axisLine={false}
            unit=" kWh"
            width={80}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: '13px', paddingTop: '12px' }}
          />
          <Line
            type="monotone"
            dataKey="generation"
            name="Generation"
            stroke="#f59e0b"
            strokeWidth={2.5}
            dot={{ r: 3, fill: '#f59e0b' }}
            activeDot={{ r: 5 }}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="creditableExport"
            name="Creditable Export"
            stroke="#3b82f6"
            strokeWidth={2.5}
            dot={{ r: 3, fill: '#3b82f6' }}
            activeDot={{ r: 5 }}
            connectNulls
          />
        </LineChart>
      </div>
    </div>
  )
}
