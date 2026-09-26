// src/api/client.js
// Centralised API helper. All fetch calls go through here.
// BASE_URL points to /api which Vite's dev proxy rewrites to http://localhost:8000.
// Change BASE_URL here if the backend moves.

const BASE_URL = '/api'

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)

  const res = await fetch(`${BASE_URL}${path}`, opts)
  if (res.status === 204) return null   // DELETE returns no body
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Request failed')
  return data
}

// --- Users ---
export const getUsers = () => request('GET', '/users')
export const createUser = (body) => request('POST', '/users', body)
export const deleteUser = (id) => request('DELETE', `/users/${id}`)

// --- Categories ---
export const getCategories = () => request('GET', '/categories')
export const createCategory = (body) => request('POST', '/categories', body)
export const deleteCategory = (id) => request('DELETE', `/categories/${id}`)

// --- Tickets ---
export const getService_requests = (params = '') => request('GET', `/service_request${params}`)
export const getService_request = (id) => request('GET', `/service_requests/${id}`)
export const createService_request = (body) => request('POST', '/service_requests', body)
export const deleteService_request = (id) => request('DELETE', `/service_requests/${id}`)
export const assignService_request = (id, body) => request('PATCH', `/service_requests/${id}/assign`, body)
export const updateService_requestStatus = (id, body) => request('PATCH', `/service_requests/${id}/status`, body)

// --- Comments ---
export const getComments = (service_requestId) => request('GET', `/service_requests/${service_requestId}/comments`)
export const createComment = (service_requestId, body) => request('POST', `/service_requests/${service_requestId}/comments`, body)
export const deleteComment = (service_requestId, commentId) => request('DELETE', `/service_requests/${service_requestId}/comments/${commentId}`)

// --- Attachments ---
export const getAttachments = (service_requestId) => request('GET', `/service_requests/${service_requestId}/attachments`)
export const createAttachment = (service_requestId, body) => request('POST', `/service_requests/${service_requestId}/attachments`, body)
export const deleteAttachment = (service_requestId, attachmentId) => request('DELETE', `/service_requests/${service_requestId}/attachments/${attachmentId}`)

// --- Audit Logs ---
export const getAllAuditLogs = () => request('GET', '/audit-logs')
export const getService_requestAuditLogs = (service_requestId) => request('GET', `/service_requests/${service_requestId}/audit-logs`)