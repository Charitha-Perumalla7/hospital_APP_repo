# Define the Pydantic models that the FastAPI uses to
# validate incoming request bodies
# shapes the outgoing response

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole

class UserCreate(BaseModel):
    name:str = Field(...,min_length=2,max_length=100,description="Full name of the user")
    email:EmailStr = Field(...,description="Unique email address,used as login identifier")
    password:str = Field(...,min_length=8,description="Password")
    role: UserRole = Field(default=UserRole.DEPARTMENT_STAFF,description="one of: Department_staff, support_engineer, team_lead, admin")

class UserResponse(BaseModel):
    # Shape the user as returned by the API
    id: str
    name: str
    email: EmailStr
    role: UserRole
    created_at: datetime