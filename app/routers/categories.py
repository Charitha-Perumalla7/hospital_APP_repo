# app/routers/categories.py
#
# Purpose:
#   HTTP endpoints for the Category entity.
#   GET    /categories        -> list all categories
#   GET    /categories/{id}   -> read one category
#   POST   /categories        -> create a category
#   PUT    /categories/{id}   -> update a category
#   DELETE /categories/{id}   -> remove a category
#
# Same ID pattern as Sub-phase 1.3 (User): each document has a self-generated
# UUID string "id" field instead of relying on MongoDB's ObjectId.

from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.collection import Collection

from app.dependencies import get_categories_collection
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    categories_collection: Collection = Depends(get_categories_collection),
):
    """
    Create a new category.
    POST -> create, per REST convention.
    """
    # Enforce unique category name at the application level.
    if categories_collection.find_one({"name": payload.name}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with this name already exists.",
        )

    category_doc = {
        "id": str(uuid4()),
        "name": payload.name,
        "description": payload.description,
        "created_at": datetime.utcnow(),
    }
    categories_collection.insert_one(category_doc)
    return category_doc


@router.get("", response_model=List[CategoryResponse])
def list_categories(categories_collection: Collection = Depends(get_categories_collection)):
    """
    List all categories.
    GET -> read, per REST convention.
    """
    return list(categories_collection.find())


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: str,
    categories_collection: Collection = Depends(get_categories_collection),
):
    """
    Get a single category by id.
    "category_id" is a PATH PARAMETER identifying exactly which resource to read.
    """
    category_doc = categories_collection.find_one({"id": category_id})
    if not category_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category_doc


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    payload: CategoryUpdate,
    categories_collection: Collection = Depends(get_categories_collection),
):
    """
    Update an existing category.
    PUT -> update, per REST convention.
    Only fields the client actually sent (exclude_unset=True) are changed.
    """
    existing = categories_collection.find_one({"id": category_id})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return existing

    # If name is being changed, make sure it doesn't collide with another category.
    if "name" in update_data:
        conflict = categories_collection.find_one({"name": update_data["name"], "id": {"$ne": category_id}})
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another category already uses this name.",
            )

    categories_collection.update_one({"id": category_id}, {"$set": update_data})
    updated_doc = categories_collection.find_one({"id": category_id})
    return updated_doc


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: str,
    categories_collection: Collection = Depends(get_categories_collection),
):
    """
    Delete a category by id.
    DELETE -> remove, per REST convention.
    204 No Content -> success, nothing to return in the body.
    """
    result = categories_collection.delete_one({"id": category_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return None