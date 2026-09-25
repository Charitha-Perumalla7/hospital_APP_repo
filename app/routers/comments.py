# app/routers/comments.py
#
# Purpose:
#   HTTP endpoints for the Comment entity. Comments are always nested under
#   a specific ticket, so every route here includes {ticket_id} in its path:
#
#   GET    /tickets/{ticket_id}/comments             -> list comments on a ticket
#   GET    /tickets/{ticket_id}/comments/{comment_id} -> read one comment
#   POST   /tickets/{ticket_id}/comments             -> add a comment to a ticket
#   PUT    /tickets/{ticket_id}/comments/{comment_id} -> edit a comment
#   DELETE /tickets/{ticket_id}/comments/{comment_id} -> remove a comment
#
# Same ID pattern as previous entities: each document has a self-generated
# UUID string "id" instead of relying on MongoDB's ObjectId.

from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.collection import Collection

from app.dependencies import get_comments_collection, get_service_requests_collection, get_users_collection
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse

# The prefix includes {ticket_id} so every route below is automatically
# scoped under a specific ticket, matching how the requirements describe
# comments as belonging to a ticket rather than existing independently.
router = APIRouter(prefix="/service_requests/{service_request_id}/comments", tags=["Comments"])


def _get_ticket_or_404(service_request_id: str, service_requests_collection: Collection) -> dict:
    """Small shared helper: confirms the parent ticket exists before touching its comments."""
    service_request_doc = service_requests_collection.find_one({"id": service_request_id})
    if not service_request_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")
    return service_request_doc


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    service_request_id: str,
    payload: CommentCreate,
    comments_collection: Collection = Depends(get_comments_collection),
    service_requests_collection: Collection = Depends(get_service_requests_collection),
    users_collection: Collection = Depends(get_users_collection),
):
    """Add a new comment to a ticket. POST -> create, per REST convention."""
    _get_service_request_or_404(service_request_id,service_requests_collection)

    if not users_collection.find_one({"id": payload.author_id}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="author_id does not match any existing user.",
        )

    comment_doc = {
        "id": str(uuid4()),
        "service_request_id": service_request_id,
        "author_id": payload.author_id,
        "content": payload.content,
        "created_at": datetime.utcnow(),
    }
    comments_collection.insert_one(comment_doc)
    return comment_doc


@router.get("", response_model=List[CommentResponse])
def list_comments(
    service_request_id: str,
    comments_collection: Collection = Depends(get_comments_collection),
    service_requests_collection: Collection = Depends(get_service_requests_collection),
):
    """List all comments on a ticket, oldest first. GET -> read, per REST convention."""
    _get_service_request_or_404(service_request_id, service_requests_collection)
    return list(comments_collection.find({"service_request_id": service_request_id}).sort("created_at", 1))


@router.get("/{comment_id}", response_model=CommentResponse)
def get_comment(
    service_request_id: str,
    comment_id: str,
    comments_collection: Collection = Depends(get_comments_collection),
    service_requests_collection: Collection = Depends(get_service_requests_collection),
):
    """Get a single comment on a ticket by id."""
    _get_service_request_or_404(service_request_id, service_requests_collection)
    comment_doc = comments_collection.find_one({"id": comment_id, "service_request_id": service_request_id})
    if not comment_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return comment_doc


@router.put("/{comment_id}", response_model=CommentResponse)
def update_comment(
    service_request_id: str,
    comment_id: str,
    payload: CommentUpdate,
    comments_collection: Collection = Depends(get_comments_collection),
    service_requests_collection: Collection = Depends(get_service_requests_collection),
):
    """Edit a comment's content. PUT -> update, per REST convention."""
    _get_service_request_or_404(service_request_id, service_requests_collection)
    existing = comments_collection.find_one({"id": comment_id, "service_request_id": service_request_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return existing

    comments_collection.update_one({"id": comment_id}, {"$set": update_data})
    return comments_collection.find_one({"id": comment_id})


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    service_request_id: str,
    comment_id: str,
    comments_collection: Collection = Depends(get_comments_collection),
    service_requests_collection: Collection = Depends(get_service_requests_collection),
):
    """Delete a comment. DELETE -> remove, per REST convention."""
    _get_service_request_or_404(service_request_id, service_requests_collection)
    result = comments_collection.delete_one({"id": comment_id, "service_request_id": service_request_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return None