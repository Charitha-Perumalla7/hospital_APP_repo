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
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.collection import Collection

from app.dependencies import (
    get_service_requests_collection,
    get_categories_collection,
    get_users_collection,
    get_audit_logs_collection,
)
from app.models.service_request import Service_request_Status, is_valid_transition
from app.models.audit_log import AuditAction, build_audit_log_doc
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
    audit_logs_collection: Collection = Depends(get_audit_logs_collection),
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
    # Record this creation in the audit trail.
    audit_logs_collection.insert_one(
        build_audit_log_doc(
            service_request_id=service_request_doc["id"],
            action=AuditAction.CREATED,
            performed_by=payload.created_by,
            details=f"Service request created with status '{Service_request_Status.NEW.value}'.",
        )
    )
    return service_request_doc


@router.get("", response_model=List[Service_request_Response])
def list_service_requests(
    service_requests_collection: Collection = Depends(get_service_requests_collection),
    # --- Query parameters: all optional, used to filter/control the request ---
    status_filter: Optional[Service_request_Status] = Query(default=None, alias="status", description="Filter by exact status"),
    category_id: Optional[str] = Query(default=None, description="Filter by category id"),
    assigned_to: Optional[str] = Query(default=None, description="Filter by assigned technician's user id"),
    created_by: Optional[str] = Query(default=None, description="Filter by the employee who raised the service_request"),
    skip: int = Query(default=0, ge=0, description="Number of service_requests to skip (for pagination)"),
    limit: int = Query(default=20, ge=1, le=100, description="Max number of service_requests to return (1-100)"),
):
    """
    List all tickets.
    GET -> read, per REST convention.
    (Query-parameter filtering, e.g. by status/category, is added in Sub-phase 1.9.)
    """
        # Build the MongoDB filter dict from whichever query parameters were actually provided.
    mongo_filter = {}
    if status_filter is not None:
        mongo_filter["status"] = status_filter
    if category_id is not None:
        mongo_filter["category_id"] = category_id
    if assigned_to is not None:
        mongo_filter["assigned_to"] = assigned_to
    if created_by is not None:
        mongo_filter["created_by"] = created_by

    cursor = tickets_collection.find(mongo_filter).sort("created_at", -1).skip(skip).limit(limit)
    return list(cursor)


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
    audit_logs_collection: Collection = Depends(get_audit_logs_collection),
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
    if not users_collection.find_one({"id": payload.assigned_by}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="assigned_by does not match any existing user.",
        )

    update_data = {"assigned_to": payload.assigned_to, "updated_at": datetime.utcnow()}

    status_also_changed = existing["status"] == Service_requestStatus.NEW
    if status_also_changed:
        update_data["status"] = Service_request_Status.ASSIGNED

    service_requests_collection.update_one({"id": service_request_id}, {"$set": update_data})
    # Record this assignment in the audit trail.
    details = f"Assigned to user '{payload.assigned_to}'."
    if status_also_changed:
        details += f" Status moved from '{Service_request_Status.NEW.value}' to '{Service_requestStatus.ASSIGNED.value}'."
    audit_logs_collection.insert_one(
        build_audit_log_doc(
            service_request_id=service_request_id,
            action=AuditAction.ASSIGNED,
            performed_by=payload.assigned_by,
            details=details,
        )
    )
    return service_requests_collection.find_one({"id": service_request_id})


@router.patch("/{service_request_id}/status", response_model=Service_request_Response)
def update_service_request_status(
    service_request_id: str,
    payload: Service_request_StatusUpdate,
    service_requests_collection: Collection = Depends(get_service_requests_collection),
    users_collection: Collection = Depends(get_users_collection),
    audit_logs_collection: Collection = Depends(get_audit_logs_collection),
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

    if not users_collection.find_one({"id": payload.changed_by}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="changed_by does not match any existing user.",
        )

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

    # Record this status change in the audit trail.
    audit_logs_collection.insert_one(
        build_audit_log_doc(
            service_request_id=service_request_id,
            action=AuditAction.STATUS_CHANGED,
            performed_by=payload.changed_by,
            details=f"Status changed from '{current_status.value}' to '{new_status.value}'.",
        )
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