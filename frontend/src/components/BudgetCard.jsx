import Gauge from './Gauge.jsx'
import { meta, usd, statusFromPct } from '../api.js'

export default function BudgetCard({ summary, selected, onSelect }) {
  if (!summary) return <div className="card tilt-l">Loading…</div>

  const buckets = summary.buckets.map((b) => {
    const pct = b.budget > 0 ? (b.spent / b.budget) * 100 : 0
    const over = b.spent > b.budget
    return {
      name: b.category,
      spent: b.spent,
      limit: b.budget,
      width: Math.min(pct, 100),
      status: statusFromPct(pct),
      over,
      note: over ? `${usd(b.spent - b.budget)} over` : `${usd(b.remaining)} left`,
    }
  })

  const t = summary.totals
  const opct = t.budget > 0 ? (t.spent / t.budget) * 100 : 0

  return (
    <div className="card tilt-l">
      <div className="buckets">
        {buckets.map((b) => (
          <div
            className={'brow' + (selected === b.name ? ' sel' : '')}
            key={b.name}
            onClick={() => onSelect(b.name)}
            title={selected === b.name ? 'Click to clear filter' : 'Show ' + b.name + ' expenses'}
          >
            <div>
              <div className="bn">{b.name}</div>
              <div className="bs num">{meta(b.spent, b.limit)}</div>
            </div>
            <Gauge width={b.width} status={b.status} />
            <div className="amt" style={{ color: b.over ? 'var(--ember)' : 'var(--moss-d)' }}>
              {b.note}
            </div>
          </div>
        ))}
      </div>

      <div className="proj">
        <div className="projlab">
          <span className="l">Overall</span>
          <span className="num" style={{ color: 'var(--text2)' }}>
            {usd(t.budget)} budget
          </span>
        </div>
        <Gauge width={Math.min(opct, 100)} status={statusFromPct(opct)} big />
        <div className="zspent">
          <span className="l">Spent this month</span>
          <span>
            <b className="num bigspent">{usd(t.spent)}</b>{' '}
            <span className="num" style={{ color: 'var(--text3)' }}>
              / {usd(t.budget)}
            </span>{' '}
            &middot;{' '}
            <span className="num" style={{ color: 'var(--moss-d)', fontWeight: 700 }}>
              {usd(t.remaining)} left
            </span>
          </span>
        </div>
      </div>
    </div>
  )
}
