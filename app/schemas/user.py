# Define the Pydantic models that the FastAPI uses to
# validate incoming request bodies
# shapes the outgoing response

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Data required from the client when creating a new user (POST /users)."""

    # Field(...) means this field is required; min_length/max_length are
    # simple validation rules applied automatically before our code runs.
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the user")
    email: EmailStr = Field(..., description="Unique email address, used as login identifier")
    password: str = Field(..., min_length=8, description="Plain-text password (hashed starting Phase 2)")

    # Optional field with a default value: if the client doesn't send "role",
    # every new user defaults to the lowest-privilege role.
    role: UserRole = Field(default=UserRole.EMPLOYEE, description="One of: employee, support_engineer, team_lead, admin")


class UserUpdate(BaseModel):
    """
    Data a client MAY send when updating a user (PUT /users/{id}).
    All fields are Optional — the client only sends the fields they want to change.
    """

    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    email: Optional[EmailStr] = Field(default=None)
    password: Optional[str] = Field(default=None, min_length=8)
    role: Optional[UserRole] = Field(default=None)


class UserResponse(BaseModel):
    """
    Shape of a user as returned by the API.
    Deliberately excludes the password field — it should never be sent back
    to the client, hashed or not.
    """

    id: str
    name: str
    email: EmailStr
    role: UserRole
    created_at: datetime