import { useState } from 'react'
import './HistoryTable.css'

function fmt(value, decimals = 0) {
  if (value === null || value === undefined) return '—'
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

// Group consecutive rows that share the same mergeGroup into clusters.
// Standalone rows become single-item clusters with no mergeGroup key.
function buildClusters(rows) {
  const clusters = []
  for (const row of rows) {
    const last = clusters[clusters.length - 1]
    if (row.mergeGroup && last?.mergeGroup === row.mergeGroup) {
      last.rows.push(row)
    } else {
      clusters.push({ mergeGroup: row.mergeGroup ?? null, rows: [row] })
    }
  }
  return clusters
}

export default function HistoryTable({ year, rows }) {
  const [open, setOpen] = useState(false)

  const totalGen  = rows.reduce((s, r) => s + (r.generation ?? 0), 0)
  const totalCash = rows.reduce((s, r) => s + (r.cash ?? 0), 0)

  const clusters = buildClusters(rows)

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
                <th>Total Cash (LKR)</th>
                <th>Cash Received (LKR)</th>
                <th>Merge Group</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {clusters.map((cluster) => (
                <>
                  {/* Individual month rows */}
                  {cluster.rows.map((r) => (
                    <tr
                      key={r.period}
                      className={[
                        cluster.mergeGroup ? 'row-merged' : '',
                        r.excludeTraining ? 'row-excluded' : '',
                      ].filter(Boolean).join(' ')}
                    >
                      <td className="td-month">{r.month}</td>
                      <td>{fmt(r.generation)}</td>
                      <td>{fmt(r.export)}</td>
                      <td>{fmt(r.import)}</td>
                      <td>{fmt(r.creditableExport)}</td>
                      <td>{fmt(r.totalCash, 2)}</td>
                      <td className={r.cash === null ? 'td-missing' : ''}>
                        {fmt(r.cash, 2)}
                      </td>
                      <td>
                        {r.mergeGroup && (
                          <span className={`merge-badge ${r.excludeTraining ? 'merge-badge-excluded' : ''}`}>
                            {r.mergeGroup}
                          </span>
                        )}
                      </td>
                      <td className="td-note">{r.note ?? ''}</td>
                    </tr>
                  ))}

                  {/* Combined subtotal row for merged groups */}
                  {cluster.mergeGroup && (() => {
                    const combinedGen = cluster.rows.reduce((s, r) => s + (r.generation ?? 0), 0)
                    // The row that holds the CEB values (export/import/cash) is the non-null one
                    const anchor = cluster.rows.find(r => r.export !== null) ?? cluster.rows[0]
                    return (
                      <tr key={`${cluster.mergeGroup}-subtotal`} className="row-subtotal">
                        <td className="td-subtotal-label">
                          {cluster.mergeGroup} Combined
                        </td>
                        <td className="td-subtotal-value">{fmt(combinedGen)}</td>
                        <td className="td-subtotal-value">{fmt(anchor.export)}</td>
                        <td className="td-subtotal-value">{fmt(anchor.import)}</td>
                        <td className="td-subtotal-value">{fmt(anchor.creditableExport)}</td>
                        <td className="td-subtotal-value">{fmt(anchor.totalCash, 2)}</td>
                        <td className="td-subtotal-value">{fmt(anchor.cash, 2)}</td>
                        <td colSpan={2} className="td-subtotal-note">
                          Used as one training unit — generation is the sum of both months
                        </td>
                      </tr>
                    )
                  })()}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
