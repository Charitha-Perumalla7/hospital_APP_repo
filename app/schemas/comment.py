# app/schemas/comment.py
#
# Purpose:
#   Defines the Pydantic models for the Comment entity.
#   A comment always belongs to exactly one ticket (the ticket_id comes from
#   the URL path, not the request body — see app/routers/comments.py).
#
# Concepts demonstrated here (same pattern as previous entities):
#   - Request models   -> CommentCreate, CommentUpdate
#   - Field validation -> min_length/max_length rules
#   - Response models  -> CommentResponse defines the API's output shape

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    """Data required from the client when adding a comment to a ticket."""

    author_id: str = Field(..., description="id of the User writing this comment")
    content: str = Field(..., min_length=1, max_length=1000, description="The comment text")


class CommentUpdate(BaseModel):
    """Data a client MAY send when editing a comment. Only content can be edited."""

    content: Optional[str] = Field(default=None, min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    """Shape of a comment as returned by the API."""

    id: str
    service_request_id: str
    author_id: str
    content: str
    created_at: datetime