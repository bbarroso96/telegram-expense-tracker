import { useState, useEffect } from 'react'
import BudgetCard from './BudgetCard.jsx'
import SavingsCard from './SavingsCard.jsx'
import Expenses from './Expenses.jsx'
import { monthLabel, weekLabel, money } from '../api.js'

export default function Home({ month, summary, expenses, categories, onChanged }) {
  // Which budget bucket is "highlighted" and filtering the ledger (null = none).
  const [bucket, setBucket] = useState(null)
  useEffect(() => { setBucket(null) }, [month])
  const toggleBucket = (name) => setBucket((b) => (b === name ? null : name))

  // Net total per week (excludes fixed/week 0) for the totals strip up top.
  const currentWeek = summary?.current_week
  const weekTotals = (summary?.weeks ?? []).map((w) => ({
    w,
    total: expenses.filter((r) => r.week === w).reduce((a, r) => a + r.cost, 0),
  }))

  return (
    <section>
      {/* marginalia doodles (wide viewports only) */}
      <svg className="marginalia m-coin" width="54" height="54" viewBox="0 0 54 54" fill="none" aria-hidden="true">
        <path
          d="M27 5 C 14 4, 4 14, 5 27 C 6 41, 15 50, 28 49 C 41 48, 50 39, 49 26 C 48 13, 39 6, 27 5 Z"
          stroke="currentColor"
          strokeWidth="2.4"
          fill="none"
        />
        <path
          d="M31 17 C 25 14, 19 18, 20 23 C 21 28, 32 27, 33 32 C 34 38, 26 41, 21 37 M26 12 L 26 43"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          fill="none"
        />
      </svg>
      <svg className="marginalia m-star" width="46" height="46" viewBox="0 0 46 46" fill="none" aria-hidden="true">
        <path
          d="M23 6 L 23 40 M8 14 L 38 32 M38 13 L 9 33"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
          fill="none"
        />
      </svg>

      <div className="headrow">
        <div>
          <h1>{monthLabel(month)}</h1>
          <svg className="squig" width="190" height="12" viewBox="0 0 190 12" fill="none" aria-hidden="true">
            <path
              d="M3 8 Q 18 2, 35 7 T 70 6 T 105 7 T 140 5 T 187 7"
              stroke="#BF0603"
              strokeWidth="3"
              strokeLinecap="round"
              fill="none"
            />
          </svg>
          <p className="sub">Household budget &amp; expenses</p>
        </div>
        {weekTotals.length > 0 && (
          <div className="weektotals">
            {weekTotals.map(({ w, total }) => (
              <div className="wt" key={w}>
                <div className="wl">{weekLabel(w, currentWeek)}</div>
                <div className="wv" style={{ color: total >= 0 ? 'var(--moss-d)' : 'var(--ember)' }}>
                  {money(total)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="cols">
        <div className="colleft">
          <p className="sec">Budget</p>
          <BudgetCard summary={summary} selected={bucket} onSelect={toggleBucket} />
          <p className="sec" style={{ marginTop: '20px' }}>Savings</p>
          <SavingsCard summary={summary} />
          <svg
            className="doodle doodle-arrow"
            width="300"
            height="74"
            viewBox="0 0 300 74"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M28 10 C 40 48, 120 66, 268 44"
              stroke="currentColor"
              strokeWidth="2.6"
              strokeLinecap="round"
              strokeDasharray="1 7"
              fill="none"
            />
            <path
              d="M252 36 L 270 44 L 250 54"
              stroke="currentColor"
              strokeWidth="2.6"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
          </svg>
        </div>

        <Expenses
          key={`${month}#${currentWeek ?? ''}`}
          expenses={expenses}
          weeks={summary?.weeks ?? []}
          currentWeek={summary?.current_week}
          categories={categories}
          onChanged={onChanged}
          bucket={bucket}
          onClearBucket={() => setBucket(null)}
        />
      </div>
    </section>
  )
}
