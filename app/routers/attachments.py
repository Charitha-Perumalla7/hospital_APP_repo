# app/routers/attachments.py
#
# Purpose:
#   HTTP endpoints for the Attachment entity (file metadata only — no real
#   file storage engine, as planned). Always nested under a specific ticket:
#
#   GET    /tickets/{ticket_id}/attachments               -> list a ticket's attachments
#   GET    /tickets/{ticket_id}/attachments/{attachment_id} -> read one
#   POST   /tickets/{ticket_id}/attachments               -> record a new attachment
#   PUT    /tickets/{ticket_id}/attachments/{attachment_id} -> fix metadata (filename/url)
#   DELETE /tickets/{ticket_id}/attachments/{attachment_id} -> remove
#
# Same ID pattern as previous entities (self-generated UUID string "id").
# Note: HttpUrl values are converted to plain strings before being stored,
# since MongoDB (via PyMongo) stores plain BSON types, not Pydantic objects.

from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.collection import Collection

from app.dependencies import get_attachments_collection, get_service_requests_collection, get_users_collection
from app.schemas.attachment import AttachmentCreate, AttachmentUpdate, AttachmentResponse

router = APIRouter(prefix="/service_requests/{service_request_id}/attachments", tags=["Attachments"])


def _get_service_request_or_404(service_request_id: str, service_requests_collection: Collection) -> dict:
    """Small shared helper: confirms the parent service_request exists before touching its attachments."""
    service_request_doc = service_requests_collection.find_one({"id": service_request_id})
    if not service_request_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")
    return service_request_doc


@router.post("", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
def create_attachment(
    service_request_id: str,
    payload: AttachmentCreate,
    attachments_collection: Collection = Depends(get_attachments_collection),
    service_requests_collection: Collection = Depends(get_service_requests_collection),
    users_collection: Collection = Depends(get_users_collection),
):
    """Record a new attachment on a service_request. POST -> create, per REST convention."""
    _get_service_request_or_404(service_request_id, service_requests_collection)

    if not users_collection.find_one({"id": payload.uploaded_by}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="uploaded_by does not match any existing user.",
        )

    attachment_doc = {
        "id": str(uuid4()),
        "service_request_id": service_request_id,
        "uploaded_by": payload.uploaded_by,
        "filename": payload.filename,
        "url": str(payload.url),  # stored as plain string; HttpUrl is a Pydantic-only type
        "size": payload.size,
        "created_at": datetime.utcnow(),
    }
    attachments_collection.insert_one(attachment_doc)
    return attachment_doc


@router.get("", response_model=List[AttachmentResponse])
def list_attachments(
    service_request_id: str,
    attachments_collection: Collection = Depends(get_attachments_collection),
    service_requests_collection: Collection = Depends(get_service_requests_collection),
):
    """List all attachments on a service_request, oldest first. GET -> read, per REST convention."""
    _get_service_request_or_404(service_request_id, service_requests_collection)
    return list(attachments_collection.find({"service_request_id": service_request_id}).sort("created_at", 1))


@router.get("/{attachment_id}", response_model=AttachmentResponse)
def get_attachment(
    service_request_id: str,
    attachment_id: str,
    attachments_collection: Collection = Depends(get_attachments_collection),
    service_requests_collection: Collection = Depends(get_service_requests_collection),
):
    """Get a single attachment on a service_request by id."""
    _get_service_request_or_404(service_request_id, service_requests_collection)
    attachment_doc = attachments_collection.find_one({"id": attachment_id, "service_request_id": service_request_id})
    if not attachment_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    return attachment_doc


@router.put("/{attachment_id}", response_model=AttachmentResponse)
def update_attachment(
    service_request_id: str,
    attachment_id: str,
    payload: AttachmentUpdate,
    attachments_collection: Collection = Depends(get_attachments_collection),
    service_requests_collection: Collection = Depends(get_service_requests_collection),
):
    """
    Fix attachment metadata (filename/url only — size and the uploader are
    never changed after creation). PUT -> update, per REST convention.
    """
    _get_service_request_or_404(service_request_id, service_requests_collection)
    existing = attachments_collection.find_one({"id": attachment_id, "service_request_id": service_request_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return existing

    if "url" in update_data:
        update_data["url"] = str(update_data["url"])  # HttpUrl -> plain string for storage

    attachments_collection.update_one({"id": attachment_id}, {"$set": update_data})
    return attachments_collection.find_one({"id": attachment_id})


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    service_request_id: str,
    attachment_id: str,
    attachments_collection: Collection = Depends(get_attachments_collection),
    service_requests_collection: Collection = Depends(get_service_requests_collection),
):
    """Delete an attachment. DELETE -> remove, per REST convention."""
    _get_service_request_or_404(service_request_id, service_requests_collection)
    result = attachments_collection.delete_one({"id": attachment_id, "service_request_id": service_request_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    return None