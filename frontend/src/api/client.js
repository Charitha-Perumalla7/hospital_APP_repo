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

// --- Service Requests ---
export const getServiceRequests = (params = '') =>
  request('GET', `/service_requests${params}`)

export const getServiceRequest = (id) =>
  request('GET', `/service_requests/${id}`)

export const createServiceRequest = (body) =>
  request('POST', '/service_requests', body)

export const deleteServiceRequest = (id) =>
  request('DELETE', `/service_requests/${id}`)

export const assignServiceRequest = (id, body) =>
  request('PATCH', `/service_requests/${id}/assign`, body)

export const updateServiceRequestStatus = (id, body) =>
  request('PATCH', `/service_requests/${id}/status`, body)

// --- Comments ---
export const getComments = (serviceRequestId) =>
  request('GET', `/service_requests/${serviceRequestId}/comments`)

export const createComment = (serviceRequestId, body) =>
  request('POST', `/service_requests/${serviceRequestId}/comments`, body)

export const deleteComment = (serviceRequestId, commentId) =>
  request(
    'DELETE',
    `/service_requests/${serviceRequestId}/comments/${commentId}`
  )

// --- Attachments ---
export const getAttachments = (serviceRequestId) =>
  request('GET', `/service_requests/${serviceRequestId}/attachments`)

export const createAttachment = (serviceRequestId, body) =>
  request('POST', `/service_requests/${serviceRequestId}/attachments`, body)

export const deleteAttachment = (serviceRequestId, attachmentId) =>
  request(
    'DELETE',
    `/service_requests/${serviceRequestId}/attachments/${attachmentId}`
  )

// --- Audit Logs ---
export const getAllAuditLogs = () =>
  request('GET', '/audit-logs')

export const getServiceRequestAuditLogs = (serviceRequestId) =>
  request(
    'GET',
    `/service_requests/${serviceRequestId}/audit-logs`
  )