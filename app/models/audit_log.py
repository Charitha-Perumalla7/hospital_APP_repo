# app/models/audit_log.py
#
# Purpose:
#   Describes the shape of an "audit_log" document as stored in MongoDB.
#   Audit logs are NEVER created directly by a client through a POST
#   endpoint — they are automatically written by the service_request router
#   whenever a service_request is created, assigned, or changes status
#   (see app/routers/service_requests.py).
#
# An audit_log document in MongoDB looks like this:
#   {
#       "id": "「uuid4 string」",
#       "service_request_id": "「service_request's uuid4 string」",
#       "action": "status_changed",
#       "performed_by": "「user's uuid4 string」",
#       "details": "Status changed from 'new' to 'assigned'",
#       "created_at": "2026-09-22T10:00:00"
#   }

from datetime import datetime
from enum import Enum
from uuid import uuid4


class AuditAction(str, Enum):
    """The fixed set of ticket events that get recorded in the audit trail."""
    CREATED = "created"
    ASSIGNED = "assigned"
    STATUS_CHANGED = "status_changed"


def build_audit_log_doc(service_request_id: str, action: AuditAction, performed_by: str, details: str) -> dict:
    """
    Builds one audit log document ready to insert into MongoDB.
    Centralizing this here means every place that writes an audit log
    (see app/routers/service_requests.py) produces a document with the exact same
    shape, instead of repeating the same dict-building code three times.
    """
    return {
        "id": str(uuid4()),
        "service_request_id": service_request_id,
        "action": action,
        "performed_by": performed_by,
        "details": details,
        "created_at": datetime.utcnow(),
    }