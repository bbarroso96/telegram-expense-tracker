import { usd, dollars } from '../api.js'

// Savings = net income (income + tax) − deduction.
// Ongoing month: deduct max(budget, spent) → a target that overspending erodes.
// Ended month: deduct actual spent → unspent budget is banked as real savings.
export default function SavingsCard({ summary }) {
  if (!summary) return null
  const t = summary.totals
  const income = t.income ?? 0
  const net = t.not_budgeted ?? 0
  const out = net - income // tax / other not-budgeted outflows (negative)
  const savings = t.savings ?? 0
  const basis = t.savings_basis ?? 'budget'
  const isCurrent = summary.is_current ?? true

  const deducted = basis === 'budget' ? (t.budget ?? 0) : (t.spent ?? 0)
  const deductedLabel = basis === 'budget' ? 'Total budget' : 'Total spent'
  const bottomLabel = isCurrent ? 'Target saving' : 'Saved this month'
  const overBudget = isCurrent && basis === 'spent'
  const signed = (n) => (n < 0 ? '-' : '') + usd(Math.abs(n))

  return (
    <div className="card savings">
      <div className="srow">
        <div>
          <div className="sn">Net income</div>
          <div className="ss num">income {usd(income)} · tax {dollars(out)}</div>
        </div>
        <div className="samt num">{usd(net)}</div>
      </div>
      <div className="srow">
        <div className="sn">{deductedLabel}</div>
        <div className="samt num" style={{ color: overBudget ? 'var(--ember)' : 'var(--text2)' }}>
          −{usd(deducted)}
        </div>
      </div>
      <div className="starget">
        <span className="l">{bottomLabel}</span>
        <span className="num bigspent" style={{ color: savings >= 0 ? 'var(--moss-d)' : 'var(--ember)' }}>
          {signed(savings)}
        </span>
      </div>
      {overBudget && (
        <div className="ss" style={{ color: 'var(--ember)', marginTop: '6px' }}>
          Over budget — eating into your target saving.
        </div>
      )}
    </div>
  )
}
