import { useState, useRef } from 'react'
import { api, usd, dollars } from '../api.js'

const IconBtn = ({ name, onClick, label }) => (
  <button className="ico" aria-label={label} onClick={onClick}>
    <i className={'ti ti-' + name} />
  </button>
)
const Trash = ({ onClick }) => <IconBtn name="trash" onClick={onClick} label="Delete" />

// Native drag-and-drop reordering. `keys` is the ordered list; on drop we POST
// the new order to `endpoint` and refresh. A grip handle is the drag source so
// the row's buttons/inputs stay clickable.
function useReorder(keys, endpoint, onChanged) {
  const dragKey = useRef(null)
  const [overKey, setOverKey] = useState(null)

  const commit = async (to) => {
    const from = dragKey.current
    dragKey.current = null
    setOverKey(null)
    if (from == null || from === to) return
    const next = keys.filter((k) => k !== from)
    const idx = next.indexOf(to)
    next.splice(idx < 0 ? next.length : idx, 0, from)
    await api.post(endpoint, { order: next })
    onChanged()
  }

  const handleProps = (key) => ({
    draggable: true,
    onDragStart: (e) => {
      dragKey.current = key
      e.dataTransfer.effectAllowed = 'move'
      const row = e.currentTarget.closest('.listrow')
      if (row) e.dataTransfer.setDragImage(row, 20, 16)
    },
    onDragEnd: () => { dragKey.current = null; setOverKey(null) },
  })
  const dropProps = (key) => ({
    onDragEnter: () => { if (dragKey.current != null && key !== dragKey.current) setOverKey(key) },
    onDragOver: (e) => e.preventDefault(),
    onDrop: (e) => { e.preventDefault(); commit(key) },
  })
  const overClass = (key) => (overKey === key ? ' dragover' : '')
  return { handleProps, dropProps, overClass }
}

const Handle = (props) => (
  <span className="handle" aria-label="Drag to reorder" {...props}>
    <i className="ti ti-grip-vertical" />
  </span>
)

function CardShell({ icon, title, adding, setAdding, addRow, children }) {
  return (
    <div className="card">
      <div className="cardhdr">
        <span>
          <i className={'ti ti-' + icon} />
          {title}
        </span>
        <button className="ico" aria-label={'Add to ' + title} onClick={() => setAdding((a) => !a)}>
          <i className="ti ti-plus" />
        </button>
      </div>
      {adding && <div style={{ marginBottom: 10 }}>{addRow}</div>}
      <div>{children}</div>
    </div>
  )
}

function BucketSelect({ value, buckets, onChange }) {
  return (
    <select className="bucketsel" value={value || ''} onChange={(e) => onChange(e.target.value)}>
      <option value="">Not budgeted</option>
      {buckets.map((b) => (<option key={b}>{b}</option>))}
    </select>
  )
}

const editGrid = (cols) => ({ display: 'grid', gridTemplateColumns: cols, gap: 8, width: '100%', alignItems: 'center' })

function CategoriesCard({ items, buckets, onChanged }) {
  const [adding, setAdding] = useState(false)
  const [name, setName] = useState('')
  const [bucket, setBucket] = useState('')
  const [editKey, setEditKey] = useState(null)
  const [draft, setDraft] = useState({ name: '', bucket: '' })
  const dnd = useReorder(items.map((c) => c.type), '/api/categories/reorder', onChanged)

  const add = async () => {
    if (!name.trim()) return
    await api.post('/api/categories', { type: name.trim(), bucket: bucket || null })
    setName(''); setBucket(''); setAdding(false); onChanged()
  }
  const setBkt = async (type, b) => { await api.put('/api/categories', { type, bucket: b || null }); onChanged() }
  const del = async (c) => { await api.del('/api/categories/' + encodeURIComponent(c)); onChanged() }
  const startEdit = (c) => { setEditKey(c.type); setDraft({ name: c.type, bucket: c.bucket || '' }) }
  const saveEdit = async (oldType) => {
    if (!draft.name.trim()) return
    await api.put('/api/categories', { old: oldType, type: draft.name.trim(), bucket: draft.bucket || null })
    setEditKey(null); onChanged()
  }

  return (
    <CardShell icon="category" title="Categories" adding={adding} setAdding={setAdding}
      addRow={
        <div style={editGrid('1fr 1fr auto')}>
          <input placeholder="New category" value={name} onChange={(e) => setName(e.target.value)} />
          <BucketSelect value={bucket} buckets={buckets} onChange={setBucket} />
          <button className="btn primary" onClick={add}><i className="ti ti-check" /></button>
        </div>
      }>
      {items.map((c) =>
        editKey === c.type ? (
          <div className="listrow" key={c.type}>
            <div style={editGrid('1fr 1fr auto auto')}>
              <input value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
              <BucketSelect value={draft.bucket} buckets={buckets} onChange={(b) => setDraft({ ...draft, bucket: b })} />
              <IconBtn name="check" onClick={() => saveEdit(c.type)} label="Save" />
              <IconBtn name="x" onClick={() => setEditKey(null)} label="Cancel" />
            </div>
          </div>
        ) : (
          <div className={'listrow' + dnd.overClass(c.type)} key={c.type} {...dnd.dropProps(c.type)}>
            <span className="leftgroup">
              <Handle {...dnd.handleProps(c.type)} />
              <span>{c.type}</span>
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <BucketSelect value={c.bucket} buckets={buckets} onChange={(b) => setBkt(c.type, b)} />
              <IconBtn name="edit" onClick={() => startEdit(c)} label="Edit" />
              <Trash onClick={() => del(c.type)} />
            </span>
          </div>
        )
      )}
    </CardShell>
  )
}

function BudgetTargetsCard({ items, onChanged }) {
  const [adding, setAdding] = useState(false)
  const [cat, setCat] = useState('')
  const [amt, setAmt] = useState('')
  const [editKey, setEditKey] = useState(null)
  const [draft, setDraft] = useState({ name: '', amt: '' })
  const dnd = useReorder(Object.keys(items), '/api/budget/reorder', onChanged)

  const add = async () => {
    if (!cat.trim()) return
    await api.put('/api/budget', { category: cat.trim(), amount: parseFloat(amt) || 0 })
    setCat(''); setAmt(''); setAdding(false); onChanged()
  }
  const del = async (c) => { await api.del('/api/budget/' + encodeURIComponent(c)); onChanged() }
  const startEdit = (c, a) => { setEditKey(c); setDraft({ name: c, amt: String(a) }) }
  const saveEdit = async (oldCat) => {
    if (!draft.name.trim()) return
    await api.put('/api/budget', { old: oldCat, category: draft.name.trim(), amount: parseFloat(draft.amt) || 0 })
    setEditKey(null); onChanged()
  }

  return (
    <CardShell icon="target" title="Budget targets" adding={adding} setAdding={setAdding}
      addRow={
        <div style={editGrid('1fr 90px auto')}>
          <input placeholder="Category" value={cat} onChange={(e) => setCat(e.target.value)} />
          <input placeholder="Amount" value={amt} onChange={(e) => setAmt(e.target.value)} />
          <button className="btn primary" onClick={add}><i className="ti ti-check" /></button>
        </div>
      }>
      {Object.entries(items).map(([c, a]) =>
        editKey === c ? (
          <div className="listrow" key={c}>
            <div style={editGrid('1fr 90px auto auto')}>
              <input value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
              <input value={draft.amt} onChange={(e) => setDraft({ ...draft, amt: e.target.value })} />
              <IconBtn name="check" onClick={() => saveEdit(c)} label="Save" />
              <IconBtn name="x" onClick={() => setEditKey(null)} label="Cancel" />
            </div>
          </div>
        ) : (
          <div className={'listrow' + dnd.overClass(c)} key={c} {...dnd.dropProps(c)}>
            <span className="leftgroup">
              <Handle {...dnd.handleProps(c)} />
              <span>{c}</span>
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="num" style={{ color: 'var(--text2)' }}>{usd(a)}</span>
              <IconBtn name="edit" onClick={() => startEdit(c, a)} label="Edit" />
              <Trash onClick={() => del(c)} />
            </span>
          </div>
        )
      )}
    </CardShell>
  )
}

function DefaultsCard({ items, cats, onChanged }) {
  const [adding, setAdding] = useState(false)
  const [item, setItem] = useState('')
  const [type, setType] = useState(cats[0] || '')
  const [editKey, setEditKey] = useState(null)
  const [draft, setDraft] = useState({ item: '', type: '' })
  const dnd = useReorder(Object.keys(items), '/api/defaults/reorder', onChanged)

  const add = async () => {
    if (!item.trim()) return
    await api.put('/api/defaults', { item: item.trim(), type })
    setItem(''); setAdding(false); onChanged()
  }
  const del = async (i) => { await api.del('/api/defaults/' + encodeURIComponent(i)); onChanged() }
  const startEdit = (i, t) => { setEditKey(i); setDraft({ item: i, type: t }) }
  const saveEdit = async (oldItem) => {
    if (!draft.item.trim()) return
    await api.put('/api/defaults', { old: oldItem, item: draft.item.trim(), type: draft.type })
    setEditKey(null); onChanged()
  }

  return (
    <CardShell icon="bolt" title="Defaults" adding={adding} setAdding={setAdding}
      addRow={
        <div style={editGrid('1fr 1fr auto')}>
          <input placeholder="Merchant" value={item} onChange={(e) => setItem(e.target.value)} />
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {cats.map((o) => (<option key={o}>{o}</option>))}
          </select>
          <button className="btn primary" onClick={add}><i className="ti ti-check" /></button>
        </div>
      }>
      {Object.entries(items).map(([i, t]) =>
        editKey === i ? (
          <div className="listrow" key={i}>
            <div style={editGrid('1fr 1fr auto auto')}>
              <input value={draft.item} onChange={(e) => setDraft({ ...draft, item: e.target.value })} />
              <select value={draft.type} onChange={(e) => setDraft({ ...draft, type: e.target.value })}>
                {cats.map((o) => (<option key={o}>{o}</option>))}
              </select>
              <IconBtn name="check" onClick={() => saveEdit(i)} label="Save" />
              <IconBtn name="x" onClick={() => setEditKey(null)} label="Cancel" />
            </div>
          </div>
        ) : (
          <div className={'listrow' + dnd.overClass(i)} key={i} {...dnd.dropProps(i)}>
            <span className="leftgroup">
              <Handle {...dnd.handleProps(i)} />
              <span>{i}</span>
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="num" style={{ color: 'var(--text2)' }}>{t}</span>
              <IconBtn name="edit" onClick={() => startEdit(i, t)} label="Edit" />
              <Trash onClick={() => del(i)} />
            </span>
          </div>
        )
      )}
    </CardShell>
  )
}

function FixedCard({ items, cats, onChanged }) {
  const [adding, setAdding] = useState(false)
  const [item, setItem] = useState('')
  const [type, setType] = useState(cats[0] || '')
  const [cost, setCost] = useState('')
  const [editKey, setEditKey] = useState(null)
  const [draft, setDraft] = useState({ item: '', type: '', cost: '' })
  const dnd = useReorder(items.map((f) => f.id), '/api/fixed/reorder', onChanged)

  const add = async () => {
    if (!item.trim()) return
    await api.post('/api/fixed', { item: item.trim(), type, cost: parseFloat(cost) || 0 })
    setItem(''); setCost(''); setAdding(false); onChanged()
  }
  const del = async (id) => { await api.del('/api/fixed/' + id); onChanged() }
  const startEdit = (f) => { setEditKey(f.id); setDraft({ item: f.item, type: f.type, cost: String(f.cost) }) }
  const saveEdit = async (id) => {
    if (!draft.item.trim()) return
    await api.put('/api/fixed/' + id, { item: draft.item.trim(), type: draft.type, cost: parseFloat(draft.cost) || 0 })
    setEditKey(null); onChanged()
  }

  return (
    <CardShell icon="repeat" title="Fixed monthly" adding={adding} setAdding={setAdding}
      addRow={
        <div style={editGrid('1.4fr 1fr 80px auto')}>
          <input placeholder="Item" value={item} onChange={(e) => setItem(e.target.value)} />
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {cats.map((o) => (<option key={o}>{o}</option>))}
          </select>
          <input placeholder="±Cost" value={cost} onChange={(e) => setCost(e.target.value)} />
          <button className="btn primary" onClick={add}><i className="ti ti-check" /></button>
        </div>
      }>
      {items.map((f) =>
        editKey === f.id ? (
          <div className="listrow" key={f.id}>
            <div style={editGrid('1.4fr 1fr 80px auto auto')}>
              <input value={draft.item} onChange={(e) => setDraft({ ...draft, item: e.target.value })} />
              <select value={draft.type} onChange={(e) => setDraft({ ...draft, type: e.target.value })}>
                {cats.map((o) => (<option key={o}>{o}</option>))}
              </select>
              <input value={draft.cost} onChange={(e) => setDraft({ ...draft, cost: e.target.value })} />
              <IconBtn name="check" onClick={() => saveEdit(f.id)} label="Save" />
              <IconBtn name="x" onClick={() => setEditKey(null)} label="Cancel" />
            </div>
          </div>
        ) : (
          <div className={'listrow' + dnd.overClass(f.id)} key={f.id} {...dnd.dropProps(f.id)}>
            <span className="leftgroup">
              <Handle {...dnd.handleProps(f.id)} />
              <span>
                <div>{f.item}</div>
                <div style={{ fontSize: '13px', color: 'var(--text3)' }}>{f.type}</div>
              </span>
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="num" style={{ color: 'var(--text2)' }}>{dollars(f.cost)}</span>
              <IconBtn name="edit" onClick={() => startEdit(f)} label="Edit" />
              <Trash onClick={() => del(f.id)} />
            </span>
          </div>
        )
      )}
    </CardShell>
  )
}

export default function Settings({ settings, categories, onChanged }) {
  if (!settings) {
    return (
      <section>
        <h1>Settings</h1>
        <p className="sub">Loading…</p>
      </section>
    )
  }
  const bucketOptions = Object.keys(settings.budget)
  const catNames = categories.map((c) => c.type)
  return (
    <section>
      <h1>Settings</h1>
      <svg className="squig" width="160" height="12" viewBox="0 0 160 12" fill="none" aria-hidden="true">
        <path
          d="M3 8 Q 18 2, 35 7 T 70 6 T 105 7 T 157 6"
          stroke="#15616D"
          strokeWidth="3"
          strokeLinecap="round"
          fill="none"
        />
      </svg>
      <p className="sub">Manage categories, budgets, defaults and fixed expenses · drag the grip to reorder</p>

      <div className="grid2">
        <CategoriesCard items={settings.categories} buckets={bucketOptions} onChanged={onChanged} />
        <BudgetTargetsCard items={settings.budget} onChanged={onChanged} />
        <DefaultsCard items={settings.defaults} cats={catNames} onChanged={onChanged} />
        <FixedCard items={settings.fixed} cats={catNames} onChanged={onChanged} />
      </div>
    </section>
  )
}
