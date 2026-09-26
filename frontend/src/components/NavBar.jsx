// src/components/NavBar.jsx
// Top navigation bar shared across all pages.
// Uses Bootstrap's navbar component for minimal styling.
import { NavLink } from 'react-router-dom'

export default function NavBar() {
  return (
    <nav className="navbar navbar-expand navbar-dark bg-dark px-3">
      <span className="navbar-brand fw-bold">IT Service Desk</span>
      <div className="navbar-nav">
        {[
          ['/tickets', 'Tickets'],
          ['/users', 'Users'],
          ['/categories', 'Categories'],
          ['/audit-logs', 'Audit Logs'],
        ].map(([to, label]) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              'nav-link' + (isActive ? ' active fw-semibold' : '')
            }
          >
            {label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}