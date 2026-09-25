# app/models/ticket.py
#
# Purpose:
#   Describes the shape of a "ticket" document as stored in MongoDB, and
#   defines the ticket lifecycle rules (which status can move to which).
#
# Lifecycle (from the requirements):
#   NEW -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED
#   Plus the branch:
#   IN_PROGRESS -> ON_HOLD -> IN_PROGRESS
#
# A ticket document in MongoDB looks like this:
#   {
#       "id": "「uuid4 string」",
#       "title": "Laptop won't turn on",
#       "description": "...",
#       "category_id": "「category's uuid4 string」",
#       "status": "new",
#       "created_by": "「employee user's uuid4 string」",
#       "assigned_to": None,                # set once a Team Lead assigns a technician
#       "created_at": "2026-09-22T10:00:00",
#       "updated_at": "2026-09-22T10:00:00"
#   }

from enum import Enum


class Service_request_Status(str, Enum):
    """The fixed set of statuses a ticket can be in."""
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    CLOSED = "closed"


# ---------------------------------------------------------------------------
# ALLOWED_TRANSITIONS is the single source of truth for the ticket lifecycle.
# Key   = current status
# Value = set of statuses it is legal to move to from there
#
# This is used by the custom validation logic in app/routers/tickets.py
# (the status-transition endpoint) to reject illegal jumps, e.g. going
# straight from NEW to RESOLVED, or moving out of CLOSED.
# ---------------------------------------------------------------------------
ALLOWED_TRANSITIONS: dict[Service_request_Status, set[Service_request_Status]] = {
    Service_request_Status.NEW: {Service_request_Status.ASSIGNED},
    Service_request_Status.ASSIGNED: {Service_request_Status.IN_PROGRESS},
    Service_request_Status.IN_PROGRESS: {Service_request_Status.ON_HOLD, Service_request_Status.RESOLVED},
    Service_request_Status.ON_HOLD: {Service_request_Status.IN_PROGRESS},
    Service_request_Status.RESOLVED: {Service_request_Status.CLOSED},
    Service_request_Status.CLOSED: set(),  # CLOSED is terminal — no further transitions allowed
}


def is_valid_transition(current_status: Service_request_Status, new_status: Service_request_Status) -> bool:
    """
    Custom application-specific rule: is moving from current_status to
    new_status allowed by the ticket lifecycle?
    Used by the status-transition endpoint before writing to the database.
    """
    return new_status in ALLOWED_TRANSITIONS.get(current_status, set())