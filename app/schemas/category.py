# app/schemas/category.py
#
# Purpose:
#   Defines the Pydantic models for the Category entity.
#   Categories classify tickets (e.g. "Laptop", "Network Access", "Software").
#
# Concepts demonstrated here (same pattern as User in Sub-phase 1.3):
#   - Request models   -> CategoryCreate, CategoryUpdate
#   - Field validation -> min_length/max_length rules
#   - Optional/default -> CategoryUpdate fields default to None
#   - Response models  -> CategoryResponse defines the API's output shape

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """Data required from the client when creating a new category (POST /categories)."""

    name: str = Field(..., min_length=2, max_length=100, description="Category name, e.g. 'Laptop', 'Network'")
    description: Optional[str] = Field(default=None, max_length=300, description="Short explanation of this category")


class CategoryUpdate(BaseModel):
    """
    Data a client MAY send when updating a category (PUT /categories/{id}).
    All fields Optional — only sent fields are changed.
    """

    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=300)


class CategoryResponse(BaseModel):
    """Shape of a category as returned by the API."""

    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime