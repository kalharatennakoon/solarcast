import { useState } from 'react'
import './HistoryTable.css'

function fmt(value, decimals = 0) {
  if (value === null || value === undefined) return '—'
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export default function HistoryTable({ year, rows }) {
  const [open, setOpen] = useState(false)

  const totalGen  = rows.reduce((s, r) => s + (r.generation ?? 0), 0)
  const totalCash = rows.reduce((s, r) => s + (r.cash ?? 0), 0)

  return (
    <div className="history-table-block">
      <button className="year-toggle" onClick={() => setOpen(o => !o)}>
        <span className="year-label">{year}</span>
        <span className="year-summary">
          {totalGen.toLocaleString()} kWh generated
          &nbsp;·&nbsp;
          LKR {fmt(totalCash, 2)} received
        </span>
        <span className="toggle-icon">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="table-wrapper">
          <table className="history-table">
            <thead>
              <tr>
                <th>Month</th>
                <th>Generation (kWh)</th>
                <th>Export to CEB (kWh)</th>
                <th>Import from CEB (kWh)</th>
                <th>Creditable Export (kWh)</th>
                <th>Cash Received (LKR)</th>
                <th>Note</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.period}>
                  <td className="td-month">{r.month}</td>
                  <td>{fmt(r.generation)}</td>
                  <td>{fmt(r.export)}</td>
                  <td>{fmt(r.import)}</td>
                  <td>{fmt(r.creditableExport)}</td>
                  <td className={r.cash === null ? 'td-missing' : ''}>
                    {r.cash !== null ? fmt(r.cash, 2) : '—'}
                  </td>
                  <td className="td-note">{r.note ?? ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
