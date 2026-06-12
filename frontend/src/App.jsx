import { useState, useEffect, useCallback } from 'react'
import TopBar from './components/TopBar.jsx'
import Home from './components/Home.jsx'
import Settings from './components/Settings.jsx'
import { api } from './api.js'

export default function App() {
  const [view, setView] = useState('home')
  const [months, setMonths] = useState([])
  const [month, setMonth] = useState(null)
  const [summary, setSummary] = useState(null)
  const [expenses, setExpenses] = useState([])
  const [settings, setSettings] = useState(null)
  const [error, setError] = useState(null)

  const loadMonth = useCallback((m) => {
    if (!m) return
    Promise.all([api.get('/api/summary?month=' + m), api.get('/api/expenses?month=' + m)])
      .then(([s, e]) => { setSummary(s); setExpenses(e); setError(null) })
      .catch((e) => setError(String(e)))
  }, [])

  const loadSettings = useCallback(() => {
    Promise.all([
      api.get('/api/categories'),
      api.get('/api/budget'),
      api.get('/api/defaults'),
      api.get('/api/fixed'),
    ])
      .then(([categories, budget, defaults, fixed]) =>
        setSettings({ categories, budget, defaults, fixed }))
      .catch((e) => setError(String(e)))
  }, [])

  // initial load: months (pick the newest) + settings
  useEffect(() => {
    api.get('/api/months')
      .then((ms) => { setMonths(ms); setMonth(ms[0] ?? null) })
      .catch((e) => setError(String(e)))
    loadSettings()
  }, [loadSettings])

  useEffect(() => { loadMonth(month) }, [month, loadMonth])

  // after a settings change, reload settings AND the month (budgets/fixed affect it)
  const onSettingsChanged = () => { loadSettings(); loadMonth(month) }

  return (
    <>
      {/* SVG turbulence filter that gives the budget highlighter its rough, hand-drawn edge */}
      <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden="true">
        <filter id="rough" x="-25%" y="-30%" width="150%" height="160%">
          <feTurbulence type="fractalNoise" baseFrequency="0.012 0.06" numOctaves="2" seed="7" result="n" />
          <feDisplacementMap in="SourceGraphic" in2="n" scale="7" xChannelSelector="R" yChannelSelector="G" />
        </filter>
      </svg>
      <TopBar
        active={view === 'settings'}
        onToggle={() => setView((v) => (v === 'home' ? 'settings' : 'home'))}
        months={months}
        month={month}
        onMonth={(m) => { setMonth(m); setView('home') }}
      />
      <main>
        {error && (
          <div className="card" style={{ margin: '16px 0', color: 'var(--ember)' }}>
            Couldn’t reach the API ({error}). Is the backend running? Start it with{' '}
            <code>python -m uvicorn api.app:app --reload</code>.
          </div>
        )}
        {view === 'home' ? (
          <Home
            month={month}
            summary={summary}
            expenses={expenses}
            categories={settings?.categories ?? []}
            onChanged={() => loadMonth(month)}
          />
        ) : (
          <Settings settings={settings} categories={settings?.categories ?? []} onChanged={onSettingsChanged} />
        )}
      </main>
    </>
  )
}
