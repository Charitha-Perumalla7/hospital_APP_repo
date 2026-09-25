# app/schemas/audit_log.py
#
# Purpose:
#   Defines the Pydantic response model for the AuditLog entity.
#   There is deliberately no AuditLogCreate or AuditLogUpdate schema:
#   audit logs are written automatically by the server (see
#   app/models/audit_log.py + app/routers/tickets.py) and are never
#   created, edited, or deleted through the API — only read.

from datetime import datetime

from pydantic import BaseModel

from app.models.audit_log import AuditAction


class AuditLogResponse(BaseModel):
    """Shape of an audit log entry as returned by the API."""

    id: str
    service_request_id: str
    action: AuditAction
    performed_by: str
    details: str
    created_at: datetime