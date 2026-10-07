import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const API = '/api'
const NEXT_STATUS = { OPEN: 'IN_PROGRESS', IN_PROGRESS: 'RESOLVED', RESOLVED: 'OPEN' }
const FILTERS = ['ALL', 'OPEN', 'IN_PROGRESS', 'RESOLVED']
const label = (s) => s.replace('_', ' ').toLowerCase()

function App() {
  const [tickets, setTickets] = useState([])
  const [stats, setStats] = useState({ total: 0, open: 0, inProgress: 0, resolved: 0 })
  const [info, setInfo] = useState(null)
  const [filter, setFilter] = useState('ALL')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  async function load() {
    try {
      setError('')
      const [t, s, i] = await Promise.all([
        fetch(`${API}/tickets`), fetch(`${API}/tickets/stats`), fetch(`${API}/info`),
      ])
      if (!t.ok || !s.ok) throw new Error('Backend unavailable')
      setTickets(await t.json())
      setStats(await s.json())
      if (i.ok) setInfo(await i.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function createTicket(e) {
    e.preventDefault()
    const form = e.currentTarget
    const f = new FormData(form)
    await fetch(`${API}/tickets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: f.get('title'), description: f.get('description'),
        category: f.get('category'), priority: f.get('priority'), requester: f.get('requester'),
      }),
    })
    form.reset()
    load()
  }

  async function advance(t) {
    await fetch(`${API}/tickets/${t.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: NEXT_STATUS[t.status] }),
    })
    load()
  }

  async function remove(t) {
    await fetch(`${API}/tickets/${t.id}`, { method: 'DELETE' })
    load()
  }

  const visible = filter === 'ALL' ? tickets : tickets.filter((t) => t.status === filter)

  return (
    <div className="page">
      <header className="top">
        <div>
          <h1>HelpDesk</h1>
          <p className="muted">IT support tickets for the team</p>
        </div>
        {info && <span className="badge">v{info.version} · {info.env}</span>}
      </header>

      {error && <div className="alert">{error}. Is the backend running?</div>}

      <section className="stats">
        <Stat name="Total" value={stats.total} />
        <Stat name="Open" value={stats.open} />
        <Stat name="In progress" value={stats.inProgress} />
        <Stat name="Resolved" value={stats.resolved} />
      </section>

      <div className="layout">
        <form className="card form" onSubmit={createTicket}>
          <h2>New ticket</h2>
          <label>Title<input name="title" required maxLength="200" placeholder="e.g. Printer on 2nd floor jammed" /></label>
          <label>Description<textarea name="description" rows="3" /></label>
          <div className="row">
            <label>Category
              <select name="category" defaultValue="GENERAL">
                {['GENERAL', 'HARDWARE', 'SOFTWARE', 'NETWORK', 'ACCESS'].map((c) => <option key={c}>{c}</option>)}
              </select>
            </label>
            <label>Priority
              <select name="priority" defaultValue="MEDIUM">
                {['LOW', 'MEDIUM', 'HIGH'].map((p) => <option key={p}>{p}</option>)}
              </select>
            </label>
          </div>
          <label>Requester<input name="requester" defaultValue="Shubham" maxLength="120" /></label>
          <button className="primary">Create ticket</button>
        </form>

        <section className="card">
          <div className="card-head">
            <h2>Tickets</h2>
            <div className="filters">
              {FILTERS.map((x) => (
                <button key={x} className={filter === x ? 'selected' : ''} onClick={() => setFilter(x)}>
                  {x === 'ALL' ? 'All' : label(x)}
                </button>
              ))}
            </div>
          </div>
          {loading ? <p className="muted">Loading...</p> : (
            <table>
              <thead>
                <tr><th>#</th><th>Ticket</th><th>Category</th><th>Priority</th><th>Status</th><th></th></tr>
              </thead>
              <tbody>
                {visible.map((t) => (
                  <tr key={t.id}>
                    <td>{t.id}</td>
                    <td><b>{t.title}</b><small>{t.requester}{t.description ? ` - ${t.description}` : ''}</small></td>
                    <td>{t.category.toLowerCase()}</td>
                    <td><span className={`pill ${t.priority.toLowerCase()}`}>{t.priority.toLowerCase()}</span></td>
                    <td><span className={`pill ${t.status.toLowerCase()}`}>{label(t.status)}</span></td>
                    <td className="actions">
                      <button onClick={() => advance(t)} title="Move to next status">next</button>
                      <button onClick={() => remove(t)} title="Delete ticket">delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {!loading && !visible.length && <p className="muted">No tickets here.</p>}
        </section>
      </div>
    </div>
  )
}

function Stat({ name, value }) {
  return <div className="card stat"><small>{name}</small><strong>{value}</strong></div>
}

createRoot(document.getElementById('root')).render(<App />)
