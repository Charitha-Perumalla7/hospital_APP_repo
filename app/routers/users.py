from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.collection import Collection

from app.dependencies import get_users_collection
from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    users_collection: Collection = Depends(get_users_collection),
):
    """
    Create a new user.
    POST -> create, per REST convention.
    Request body is validated automatically against UserCreate.
    """
    # Enforce unique email at the application level (simple find, no unique index yet).
    if users_collection.find_one({"email": payload.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    # Build the MongoDB document from the validated request data.
    user_doc = {
        "id": str(uuid4()),
        "name": payload.name,
        "email": payload.email,
        "password": payload.password,  # stored as plain text for now; hashed from Phase 2
        "role": payload.role,
        "created_at": datetime.utcnow(),
    }
    users_collection.insert_one(user_doc)

    # response_model=UserResponse automatically drops the "password" field
    # from what gets sent back to the client.
    return user_doc


@router.get("", response_model=List[UserResponse])
def list_users(users_collection: Collection = Depends(get_users_collection)):
    """
    List all users.
    GET -> read, per REST convention.
    """
    return list(users_collection.find())


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    users_collection: Collection = Depends(get_users_collection),
):
    """
    Get a single user by id.
    "user_id" here is a PATH PARAMETER — it identifies exactly which resource to read.
    """
    user_doc = users_collection.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_doc


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserUpdate,
    users_collection: Collection = Depends(get_users_collection),
):
    """
    Update an existing user.
    PUT -> update, per REST convention.
    Only fields the client actually sent (exclude_unset=True) are changed —
    everything else on the existing document is left untouched.
    """
    existing = users_collection.find_one({"id": user_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        # Nothing to update — just return the existing user as-is.
        return existing

    # If email is being changed, make sure it doesn't collide with another user.
    if "email" in update_data:
        conflict = users_collection.find_one({"email": update_data["email"], "id": {"$ne": user_id}})
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another user already uses this email.",
            )

    users_collection.update_one({"id": user_id}, {"$set": update_data})
    updated_doc = users_collection.find_one({"id": user_id})
    return updated_doc


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    users_collection: Collection = Depends(get_users_collection),
):
    """
    Delete a user by id.
    DELETE -> remove, per REST convention.
    204 No Content -> success, but there is nothing to return in the body.
    """
    result = users_collection.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return None