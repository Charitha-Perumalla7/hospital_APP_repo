# app/schemas/ticket.py
#
# Purpose:
#   Defines the Pydantic models for the Ticket entity. Tickets are split
#   into several narrow input schemas (instead of one big "update everything"
#   schema) because different roles change different things:
#     - TicketCreate       -> Employee raises a new ticket
#     - TicketUpdate       -> edit ticket details (title/description/category)
#     - TicketAssign       -> Team Lead assigns/reassigns a technician
#     - TicketStatusUpdate -> Support Engineer/Team Lead moves the ticket
#                             through its lifecycle (NEW -> ASSIGNED -> ...)
#
# Concepts demonstrated here (from the Phase 1 requirement list):
#   - Field validation  -> Field(...) rules below
#   - Custom validators -> field_validator on title/description (reject blank text)
#   - Optional/default  -> TicketUpdate fields default to None

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.service_request import Service_request_Status


class Service_request_Create(BaseModel):
    """Data required from the client when raising a new ticket (POST /tickets)."""

    title: str = Field(..., min_length=3, max_length=150, description="Short summary of the issue")
    description: str = Field(..., min_length=5, max_length=2000, description="Full details of the issue")
    category_id: str = Field(..., description="id of an existing Category")
    created_by: str = Field(..., description="id of the Department Staff raising this ticket")

    @field_validator("title", "description")
    @classmethod
    def not_blank(cls, value: str) -> str:
        """
        Custom validator: rejects a title/description that is empty or only
        whitespace (e.g. "   "), which Field(min_length=...) alone would not catch
        since it counts whitespace characters too.
        """
        if not value.strip():
            raise ValueError("This field cannot be blank or just whitespace.")
        return value.strip()


class Service_request_Update(BaseModel):
    """
    Edit ticket details (NOT status or assignment — those have their own
    dedicated endpoints/schemas below). All fields Optional.
    """

    title: Optional[str] = Field(default=None, min_length=3, max_length=150)
    description: Optional[str] = Field(default=None, min_length=5, max_length=2000)
    category_id: Optional[str] = Field(default=None)


class Service_request_Assign(BaseModel):
    """Used by a Team Lead to assign or reassign a technician to a ticket."""

    assigned_to: str = Field(..., description="id of the Support Engineer to assign")


class Service_request_StatusUpdate(BaseModel):
    """
    Used to move a ticket through its lifecycle.
    Note: this schema only checks that "status" is one of the valid enum
    values. Whether the specific FROM -> TO move is legal (e.g. you can't
    jump from NEW straight to RESOLVED) depends on the ticket's *current*
    status in the database, so that check happens in the router, using
    app.models.ticket.is_valid_transition().
    """

    status: Service_request_Status = Field(..., description="The status to move this Service request to")


class Service_request_Response(BaseModel):
    """Shape of a ticket as returned by the API."""

    id: str
    title: str
    description: str
    category_id: str
    status: Service_request_Status
    created_by: str
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime