// src/pages/TicketsPage.jsx
// Lists tickets with optional status filter and pagination.
// Provides a form to create a new ticket (requires at least one user and category to exist).
// Click a ticket row to open its detail page.
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getTickets, getUsers, getCategories, createTicket, deleteTicket } from '../api/client'

const STATUSES = ['', 'new', 'assigned', 'in_progress', 'on_hold', 'resolved', 'closed']

const STATUS_COLORS = {
  new: 'secondary', assigned: 'primary', in_progress: 'info',
  on_hold: 'warning', resolved: 'success', closed: 'dark',
}

const blank = { title: '', description: '', category_id: '', created_by: '' }

export default function TicketsPage() {
  const navigate = useNavigate()
  const [tickets, setTickets] = useState([])
  const [users, setUsers] = useState([])
  const [categories, setCategories] = useState([])
  const [statusFilter, setStatusFilter] = useState('')
  const [form, setForm] = useState(blank)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = (status = statusFilter) => {
    const qs = status ? `?status=${status}` : ''
    getTickets(qs).then(setTickets).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
    getUsers().then(setUsers).catch(() => {})
    getCategories().then(setCategories).catch(() => {})
  }, [])

  const handleFilter = (s) => {
    setStatusFilter(s)
    load(s)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await createTicket(form)
      setForm(blank)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleDelete = async (e, id) => {
    e.stopPropagation()
    if (!confirm('Delete this ticket?')) return
    try { await deleteTicket(id); load() } catch (err) { setError(err.message) }
  }

  return (
    <div>
      <h4>Tickets</h4>

      {/* Create ticket form */}
      <form onSubmit={handleSubmit} className="row g-2 mb-3">
        <div className="col-md-3">
          <input className="form-control form-control-sm" placeholder="Title (min 3 chars)" required minLength={3}
            value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
        </div>
        <div className="col-md-3">
          <input className="form-control form-control-sm" placeholder="Description (min 5 chars)" required minLength={5}
            value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
        </div>
        <div className="col-md-2">
          <select className="form-select form-select-sm" required value={form.category_id}
            onChange={e => setForm({ ...form, category_id: e.target.value })}>
            <option value="">-- Category --</option>
            {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="col-md-2">
          <select className="form-select form-select-sm" required value={form.created_by}
            onChange={e => setForm({ ...form, created_by: e.target.value })}>
            <option value="">-- Created By --</option>
            {users.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
          </select>
        </div>
        <div className="col-md-2">
          <button className="btn btn-sm btn-primary w-100" type="submit">Create Ticket</button>
        </div>
        {error && <div className="col-12"><small className="text-danger">{error}</small></div>}
      </form>

      {/* Status filter */}
      <div className="mb-3">
        {STATUSES.map(s => (
          <button key={s || 'all'} onClick={() => handleFilter(s)}
            className={`btn btn-sm me-1 ${statusFilter === s ? 'btn-dark' : 'btn-outline-secondary'}`}>
            {s || 'All'}
          </button>
        ))}
      </div>

      {/* Tickets table */}
      {loading ? <p>Loading…</p> : (
        <table className="table table-sm table-bordered table-hover">
          <thead className="table-dark">
            <tr><th>Title</th><th>Status</th><th>Category</th><th>Created</th><th></th></tr>
          </thead>
          <tbody>
            {tickets.length === 0 && <tr><td colSpan={5} className="text-center text-muted">No tickets.</td></tr>}
            {tickets.map(t => (
              <tr key={t.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/tickets/${t.id}`)}>
                <td>{t.title}</td>
                <td><span className={`badge bg-${STATUS_COLORS[t.status] || 'secondary'}`}>{t.status}</span></td>
                <td>{categories.find(c => c.id === t.category_id)?.name || t.category_id}</td>
                <td>{new Date(t.created_at).toLocaleDateString()}</td>
                <td onClick={e => e.stopPropagation()}>
                  <button className="btn btn-sm btn-outline-danger" onClick={(e) => handleDelete(e, t.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}