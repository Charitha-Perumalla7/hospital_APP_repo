// src/App.jsx
// Root component. Defines client-side routes using react-router-dom.
// Each route maps to a page component in src/pages/.
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import NavBar from './components/NavBar'
import UsersPage from './pages/UsersPage'
import CategoriesPage from './pages/CategoriesPage'
import ServiceRequestsPage from './pages/ServiceRequestsPage'
import ServiceRequestDetailPage from './pages/ServiceRequestDetailPage'
import AuditLogsPage from './pages/AuditLogsPage'

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />

      <div className="container mt-4">
        <Routes>
          <Route
            path="/"
            element={<Navigate to="/service_requests" replace />}
          />

          <Route
            path="/users"
            element={<UsersPage />}
          />

          <Route
            path="/categories"
            element={<CategoriesPage />}
          />

          <Route
            path="/service_requests"
            element={<ServiceRequestsPage />}
          />

          <Route
            path="/service_requests/:serviceRequestId"
            element={<ServiceRequestDetailPage />}
          />

          <Route
            path="/audit-logs"
            element={<AuditLogsPage />}
          />
        </Routes>
      </div>
    </BrowserRouter>
  )
}