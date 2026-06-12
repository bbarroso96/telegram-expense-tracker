import { monthLabel } from '../api.js'

export default function TopBar({ active, onToggle, months = [], month, onMonth }) {
  return (
    <header>
      <div className="bar">
        <div className="brand">
          <div className="mark">
            <i className="ti ti-wallet" />
          </div>
          <span>My Budget Notebook</span>
        </div>
        <div className="barright">
          <select value={month ?? ''} onChange={(e) => onMonth(e.target.value)}>
            {months.length === 0 && <option value="">—</option>}
            {months.map((m) => (
              <option key={m} value={m}>
                {monthLabel(m)}
              </option>
            ))}
          </select>
          <button
            className={'gear' + (active ? ' on' : '')}
            title="Settings"
            aria-label="Settings"
            onClick={onToggle}
          >
            <i className="ti ti-settings" />
          </button>
        </div>
      </div>
    </header>
  )
}
