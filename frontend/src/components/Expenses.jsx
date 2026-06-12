import { useState } from 'react'
import { api, money, dollars, weekLabel, defaultWeek } from '../api.js'

const sum = (arr) => arr.reduce((a, r) => a + r.cost, 0)

function WeekHeader({ label, total }) {
  const color = total >= 0 ? 'var(--moss-d)' : 'var(--ember)'
  return (
    <tr className="grouphdr">
      <td colSpan={3}>{label}</td>
      <td style={{ textAlign: 'right', color }}>{dollars(total)}</td>
      <td></td>
    </tr>
  )
}

function LedgerRow({ r, band, onEdit, onDelete }) {
  const pos = r.cost >= 0
  let cls = band != null ? 'band' + band : ''
  if (r.week === 0) cls += ' fixed'
  return (
    <tr className={cls.trim() || undefined}>
      <td className="item">{r.item}</td>
      <td style={{ textAlign: 'center' }}>
        <span className="wk">{r.week}</span>
      </td>
      <td style={{ color: 'var(--text2)' }}>{r.type}</td>
      <td className={'num' + (pos ? ' pos' : '')} style={{ textAlign: 'right' }}>
        {money(r.cost)}
      </td>
      <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
        <button className="ico" aria-label="Edit" onClick={() => onEdit(r)}>
          <i className="ti ti-edit" />
        </button>
        <button className="ico" aria-label="Delete" onClick={() => onDelete(r)}>
          <i className="ti ti-trash" />
        </button>
      </td>
    </tr>
  )
}

// Grouped ledger body. In bucket mode: all rows of that budget bucket (any
// week, incl. fixed), grouped by week. Otherwise: the week/fixed filter.
function Ledger({ rows, selected, showFixed, currentWeek, bucket, typeBucket, onEdit, onDelete }) {
  // Compose both filters: bucket narrows the category, week narrows the time.
  // Fixed (week 0) shows when "Show fixed" is on, or when viewing all weeks of a bucket.
  const showFixedRows = showFixed || (bucket && selected === 'all')
  const list = rows.filter((r) => {
    if (bucket && typeBucket[r.type] !== bucket) return false
    if (r.week === 0) return showFixedRows
    return selected === 'all' ? true : r.week === +selected
  })

  if (!list.length) {
    return (
      <tr>
        <td colSpan={5} className="empty">
          Nothing logged here yet.
        </td>
      </tr>
    )
  }

  const out = []
  let key = 0
  const fixedRows = list.filter((r) => r.week === 0)
  const weekRows = list.filter((r) => r.week !== 0)
  const includeFixed = showFixedRows && fixedRows.length > 0

  if (includeFixed) {
    out.push(<WeekHeader key={'h' + key++} label="Fixed monthly" total={sum(fixedRows)} />)
    fixedRows.forEach((r) => out.push(<LedgerRow key={'r' + r.id} r={r} onEdit={onEdit} onDelete={onDelete} />))
  }

  const grouped = selected === 'all'
  if (grouped) {
    const weeks = [...new Set(weekRows.map((r) => r.week))].sort((a, b) => a - b)
    weeks.forEach((w, i) => {
      const wr = weekRows.filter((r) => r.week === w)
      out.push(<WeekHeader key={'h' + key++} label={weekLabel(w, currentWeek)} total={sum(wr)} />)
      wr.forEach((r) => out.push(<LedgerRow key={'r' + r.id} r={r} band={i % 2} onEdit={onEdit} onDelete={onDelete} />))
    })
  } else {
    if (weekRows.length) {
      out.push(<WeekHeader key={'h' + key++} label={weekLabel(selected, currentWeek)} total={sum(weekRows)} />)
    }
    weekRows.forEach((r) => out.push(<LedgerRow key={'r' + r.id} r={r} onEdit={onEdit} onDelete={onDelete} />))
  }

  return out
}

export default function Expenses({ expenses, weeks, currentWeek, categories, onChanged, bucket, onClearBucket }) {
  const [selected, setSelected] = useState(() => defaultWeek(weeks, currentWeek))
  const [showFixed, setShowFixed] = useState(false)
  const [form, setForm] = useState(null) // null = closed; else { id?, item, week, type, cost }

  const catNames = categories.length
    ? categories.map((c) => c.type)
    : ['Food', 'Groceries', 'Leasure', 'Other', 'Bill - Gas', 'Income']
  const typeBucket = Object.fromEntries(categories.map((c) => [c.type, c.bucket]))
  const chips = [
    ...weeks.map((w) => ({ key: w, label: weekLabel(w, currentWeek) })),
    { key: 'all', label: 'All weeks' },
  ]

  // Week chips narrow the time range; they keep any active bucket filter.
  const pickWeek = (key) => setSelected(key)

  const openAdd = () => setForm({ item: '', week: currentWeek ?? 1, type: catNames[0], cost: '' })
  const openEdit = (r) => setForm({ id: r.id, item: r.item, week: r.week, type: r.type, cost: Math.abs(r.cost) })

  const save = async () => {
    const body = {
      item: form.item.trim(),
      type: form.type,
      amount: Math.abs(parseFloat(form.cost)) || 0,
      week: parseInt(form.week, 10) || 0,
    }
    if (!body.item) return
    if (form.id) await api.put('/api/expenses/' + form.id, body)
    else await api.post('/api/expenses', body)
    setForm(null)
    onChanged()
  }

  const del = async (r) => {
    await api.del('/api/expenses/' + r.id)
    onChanged()
  }

  return (
    <div className="colright">
      <p className="sec">Expenses</p>
      <div className="toolbar">
        <div className="chips">
          {bucket && (
            <button className="chip on" onClick={onClearBucket} title="Clear category filter">
              {bucket} <i className="ti ti-x" />
            </button>
          )}
          {chips.map((c) => (
            <button
              key={c.key}
              className={'chip' + (selected === c.key ? ' on' : '')}
              onClick={() => pickWeek(c.key)}
            >
              {c.label}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className={'btn' + (showFixed ? ' on' : '')} onClick={() => setShowFixed((s) => !s)}>
            <i className={'ti ' + (showFixed ? 'ti-eye-off' : 'ti-eye')} />{' '}
            {showFixed ? 'Hide fixed' : 'Show fixed'}
          </button>
          <button className="btn primary" onClick={openAdd}>
            <i className="ti ti-plus" /> Add expense
          </button>
        </div>
      </div>

      {form && (
        <div className="card addform" style={{ marginBottom: 14 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 70px 1.3fr 100px', gap: 10, alignItems: 'center' }}>
            <input
              type="text"
              placeholder="Item"
              value={form.item}
              onChange={(e) => setForm({ ...form, item: e.target.value })}
            />
            <input
              type="text"
              placeholder="Week"
              value={form.week}
              onChange={(e) => setForm({ ...form, week: e.target.value })}
            />
            <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              {catNames.map((o) => (
                <option key={o}>{o}</option>
              ))}
            </select>
            <input
              type="text"
              placeholder="Cost"
              value={form.cost}
              onChange={(e) => setForm({ ...form, cost: e.target.value })}
            />
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 14 }}>
            <button className="btn" onClick={() => setForm(null)}>
              Cancel
            </button>
            <button className="btn primary" onClick={save}>
              <i className="ti ti-check" /> Save
            </button>
          </div>
        </div>
      )}

      <div className="card" style={{ padding: '6px 4px' }}>
        <table>
          <thead>
            <tr>
              <th>Item</th>
              <th style={{ width: 64, textAlign: 'center' }}>Week</th>
              <th style={{ width: '30%' }}>Type</th>
              <th style={{ width: 110, textAlign: 'right' }}>Cost</th>
              <th style={{ width: 70 }}></th>
            </tr>
          </thead>
          <tbody>
            <Ledger
              rows={expenses}
              selected={selected}
              showFixed={showFixed}
              currentWeek={currentWeek}
              bucket={bucket}
              typeBucket={typeBucket}
              onEdit={openEdit}
              onDelete={del}
            />
          </tbody>
        </table>
      </div>
    </div>
  )
}
