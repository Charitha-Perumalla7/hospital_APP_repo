// src/App.jsx
// Root component. Defines client-side routes using react-router-dom.
// Each route maps to a page component in src/pages/.
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import NavBar from './components/NavBar'
import UsersPage from './pages/UsersPage'
import CategoriesPage from './pages/CategoriesPage'
import TicketsPage from './pages/TicketsPage'
import TicketDetailPage from './pages/TicketDetailPage'
import AuditLogsPage from './pages/AuditLogsPage'

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <div className="container mt-4">
        <Routes>
          <Route path="/" element={<Navigate to="/tickets" replace />} />
          <Route path="/users" element={<UsersPage />} />
          <Route path="/categories" element={<CategoriesPage />} />
          <Route path="/tickets" element={<TicketsPage />} />
          <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
          <Route path="/audit-logs" element={<AuditLogsPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}