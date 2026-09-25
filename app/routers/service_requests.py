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
    get_service_requests_collection,
    get_categories_collection,
    get_users_collection,
)
from app.models.service_request import Service_request_Status, is_valid_transition
from app.schemas.service_request import (
    Service_request_Create,
    Service_request_Update,
    Service_request_Assign,
    Service_request_StatusUpdate,
    Service_request_Response,
)

router = APIRouter(prefix="/service_request", tags=["Service_request"])


@router.post("", response_model=Service_request_Response, status_code=status.HTTP_201_CREATED)
def create_service_request(
    payload: Service_request_Create,
    service_requests_collection: Collection = Depends(get_service_requests_collection),
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
        "status": Service_request_Status.NEW,
        "created_by": payload.created_by,
        "assigned_to": None,
        "created_at": now,
        "updated_at": now,
    }
    service_requests_collection.insert_one(service_request_doc)
    return service_request_doc


@router.get("", response_model=List[Service_request_Response])
def list_service_request(service_requests_collection: Collection = Depends(get_service_requests_collection)):
    """
    List all tickets.
    GET -> read, per REST convention.
    (Query-parameter filtering, e.g. by status/category, is added in Sub-phase 1.9.)
    """
    return list(service_requests_collection.find())


@router.get("/{service_request_id}", response_model=Service_request_Response)
def get_service_request(
    service_request_id: str,
    service_request_collection: Collection = Depends(get_service_requests_collection) #check this line
):
    """Get a single ticket by id ("ticket_id" is a path parameter)."""
    service_request_doc = service_requests_collection.find_one({"id": service_request_id})
    if not service_request_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")
    return service_request_doc


@router.put("/{service_request_id}", response_model=Service_request_Response)
def update_service_request(
    service_request_id: str,
    payload: Service_request_Update,
    service_requests_collection: Collection = Depends(get_service_requests_collection),
    categories_collection: Collection = Depends(get_categories_collection),
):
    """
    Update ticket details (title/description/category) only.
    Status and assignment are changed through their own dedicated endpoints
    below, so this endpoint deliberately does not touch them.
    """
    existing = service_requests_collection.find_one({"id": service_request_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return existing

    if "category_id" in update_data and not categories_collection.find_one({"id": update_data["category_id"]}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="category_id does not match any existing category.",
        )

    update_data["updated_at"] = datetime.utcnow()
    service_requests_collection.update_one({"id": service_request_id}, {"$set": update_data})
    return service_requests_collection.find_one({"id": service_request_id})


@router.patch("/{service_request_id}/assign", response_model=Service_request_Response)
def assign_service_request(
    service_request_id: str,
    payload: Service_request_Assign,
    service_requests_collection: Collection = Depends(get_service_requests_collection),
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
    existing = service_requests_collection.find_one({"id": service_request_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")

    if not users_collection.find_one({"id": payload.assigned_to}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="assigned_to does not match any existing user.",
        )

    update_data = {"assigned_to": payload.assigned_to, "updated_at": datetime.utcnow()}

    if existing["status"] == Service_request_Status.NEW:
        update_data["status"] = Service_request_Status.ASSIGNED

    service_requests_collection.update_one({"id": service_request_id}, {"$set": update_data})
    return service_requests_collection.find_one({"id": service_request_id})


@router.patch("/{service_request_id}/status", response_model=Service_request_Response)
def update_service_request_status(
    service_request_id: str,
    payload: Service_request_StatusUpdate,
    service_requests_collection: Collection = Depends(get_service_requests_collection),
):
    """
    Move a ticket through its lifecycle.
    Enforces the ALLOWED_TRANSITIONS rules from app/models/ticket.py —
    e.g. a ticket cannot jump straight from NEW to RESOLVED, and nothing
    can leave CLOSED once it gets there.
    """
    existing = service_requests_collection.find_one({"id": service_request_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")

    current_status = Service_request_Status(existing["status"])
    new_status = payload.status

    if not is_valid_transition(current_status, new_status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot move service request from '{current_status.value}' to '{new_status.value}'.",
        )

    service_requests_collection.update_one(
        {"id": service_request_id},
        {"$set": {"status": new_status, "updated_at": datetime.utcnow()}},
    )
    return service_requests_collection.find_one({"id": service_request_id})


@router.delete("/{service_request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_request(
    service_request_id: str,
    service_requests_collection: Collection = Depends(get_service_requests_collection),
):
    """Delete a ticket by id. DELETE -> remove, per REST convention."""
    result = service_requests_collection.delete_one({"id": service_request_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")
    return None