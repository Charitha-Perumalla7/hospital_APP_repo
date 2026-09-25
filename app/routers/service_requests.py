# app/routers/tickets.py
#
# Purpose:
#   HTTP endpoints for the Ticket entity — the core entity of this system.
#   GET    /tickets                  -> list all tickets
#   GET    /tickets/{id}             -> read one ticket
#   POST   /tickets                  -> create a ticket (Employee raises an issue)
#   PUT    /tickets/{id}             -> update ticket details (title/description/category)
#   PATCH  /tickets/{id}/assign      -> assign/reassign a technician (Team Lead)
#   PATCH  /tickets/{id}/status      -> move the ticket through its lifecycle
#   DELETE /tickets/{id}             -> remove a ticket
#
# Same ID pattern as previous entities: each document has a self-generated
# UUID string "id" instead of relying on MongoDB's ObjectId.

from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.collection import Collection

from app.dependencies import (
    get_tickets_collection,
    get_categories_collection,
    get_users_collection,
)
from app.models.ticket import TicketStatus, is_valid_transition
from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketAssign,
    TicketStatusUpdate,
    TicketResponse,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    tickets_collection: Collection = Depends(get_tickets_collection),
    categories_collection: Collection = Depends(get_categories_collection),
    users_collection: Collection = Depends(get_users_collection),
):
    """
    Create a new ticket.
    POST -> create, per REST convention.
    Every new ticket always starts at status NEW and unassigned — the client
    cannot set these directly, which is why they aren't fields on TicketCreate.
    """
    # Data-integrity checks: the referenced category and user must actually exist.
    if not categories_collection.find_one({"id": payload.category_id}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="category_id does not match any existing category.",
        )
    if not users_collection.find_one({"id": payload.created_by}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="created_by does not match any existing user.",
        )

    now = datetime.utcnow()
    ticket_doc = {
        "id": str(uuid4()),
        "title": payload.title,
        "description": payload.description,
        "category_id": payload.category_id,
        "status": TicketStatus.NEW,
        "created_by": payload.created_by,
        "assigned_to": None,
        "created_at": now,
        "updated_at": now,
    }
    tickets_collection.insert_one(ticket_doc)
    return ticket_doc


@router.get("", response_model=List[TicketResponse])
def list_tickets(tickets_collection: Collection = Depends(get_tickets_collection)):
    """
    List all tickets.
    GET -> read, per REST convention.
    (Query-parameter filtering, e.g. by status/category, is added in Sub-phase 1.9.)
    """
    return list(tickets_collection.find())


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: str,
    tickets_collection: Collection = Depends(get_tickets_collection),
):
    """Get a single ticket by id ("ticket_id" is a path parameter)."""
    ticket_doc = tickets_collection.find_one({"id": ticket_id})
    if not ticket_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket_doc


@router.put("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    tickets_collection: Collection = Depends(get_tickets_collection),
    categories_collection: Collection = Depends(get_categories_collection),
):
    """
    Update ticket details (title/description/category) only.
    Status and assignment are changed through their own dedicated endpoints
    below, so this endpoint deliberately does not touch them.
    """
    existing = tickets_collection.find_one({"id": ticket_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return existing

    if "category_id" in update_data and not categories_collection.find_one({"id": update_data["category_id"]}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="category_id does not match any existing category.",
        )

    update_data["updated_at"] = datetime.utcnow()
    tickets_collection.update_one({"id": ticket_id}, {"$set": update_data})
    return tickets_collection.find_one({"id": ticket_id})


@router.patch("/{ticket_id}/assign", response_model=TicketResponse)
def assign_ticket(
    ticket_id: str,
    payload: TicketAssign,
    tickets_collection: Collection = Depends(get_tickets_collection),
    users_collection: Collection = Depends(get_users_collection),
):
    """
    Assign or reassign a technician to a ticket (Team Lead responsibility).

    Lifecycle rule applied here: assigning a technician to a brand-new ticket
    naturally moves it from NEW -> ASSIGNED. If the ticket is being
    *reassigned* later on (already past NEW), we only change the technician
    and leave the current status untouched — reassignment shouldn't reset
    progress that's already been made.
    """
    existing = tickets_collection.find_one({"id": ticket_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if not users_collection.find_one({"id": payload.assigned_to}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="assigned_to does not match any existing user.",
        )

    update_data = {"assigned_to": payload.assigned_to, "updated_at": datetime.utcnow()}

    if existing["status"] == TicketStatus.NEW:
        update_data["status"] = TicketStatus.ASSIGNED

    tickets_collection.update_one({"id": ticket_id}, {"$set": update_data})
    return tickets_collection.find_one({"id": ticket_id})


@router.patch("/{ticket_id}/status", response_model=TicketResponse)
def update_ticket_status(
    ticket_id: str,
    payload: TicketStatusUpdate,
    tickets_collection: Collection = Depends(get_tickets_collection),
):
    """
    Move a ticket through its lifecycle.
    Enforces the ALLOWED_TRANSITIONS rules from app/models/ticket.py —
    e.g. a ticket cannot jump straight from NEW to RESOLVED, and nothing
    can leave CLOSED once it gets there.
    """
    existing = tickets_collection.find_one({"id": ticket_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    current_status = TicketStatus(existing["status"])
    new_status = payload.status

    if not is_valid_transition(current_status, new_status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot move ticket from '{current_status.value}' to '{new_status.value}'.",
        )

    tickets_collection.update_one(
        {"id": ticket_id},
        {"$set": {"status": new_status, "updated_at": datetime.utcnow()}},
    )
    return tickets_collection.find_one({"id": ticket_id})


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: str,
    tickets_collection: Collection = Depends(get_tickets_collection),
):
    """Delete a ticket by id. DELETE -> remove, per REST convention."""
    result = tickets_collection.delete_one({"id": ticket_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return None