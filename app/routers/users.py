from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.collection import Collection

from app.dependencies import get_users_collection
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users",tags=["users"])

# Create a new user
@router.post("",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def create_user(payload:UserCreate, users_collection:Collection = Depends(get_users_collection),):
    if users_collection.find_one({"email":payload.email}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="A user with this email already exists",)

    user_doc = {"id":str(uuid4()), "name":payload.name,"email":payload.email,
                "password":payload.password,"role":payload.role,
                "created_at":datetime.utcnow()}
    users_collection.insert_one(user_doc)
    return user_doc

# Get all users data in the list format
@router.get("",response_model=List[UserResponse])
def list_users(users_collection: Collection=Depends(get_users_collection)):
    return list(users_collection.find())