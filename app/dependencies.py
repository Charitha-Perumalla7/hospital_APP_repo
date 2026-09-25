#   Defines reusable FastAPI dependencies (functions used with Depends()).
#   Routers will import these instead of talking to app/database.py directly.
from pymongo.collection import Collection
from pymongo.database import Database
from fastapi import Depends

from app.database import database


def get_db() -> Database:
    """
    Base dependency: provides the shared MongoDB database object.
    """
    return database


# ---------------------------------------------------------------------------
# One small dependency per collection (entity).
# Each of these takes db as a nested dependency, then returns the specific
# collection a router needs. Example usage in a router:
#
#   from fastapi import Depends
#   from app.dependencies import get_users_collection
#
#   @router.get("/users")
#   def list_users(users_collection = Depends(get_users_collection)):
#       return list(users_collection.find())
# ---------------------------------------------------------------------------


def get_users_collection(db: Database = Depends(get_db)) -> Collection:
    """Provides access to the 'users' collection."""
    return db["users"]


def get_categories_collection(db: Database = Depends(get_db)) -> Collection:
    """Provides access to the 'categories' collection."""
    return db["categories"]


def get_service_requests_collection(db: Database = Depends(get_db)) -> Collection:
    """Provides access to the 'tickets' collection."""
    return db["service_request"]


def get_comments_collection(db: Database = Depends(get_db)) -> Collection:
    """Provides access to the 'comments' collection."""
    return db["comments"]


def get_attachments_collection(db: Database = Depends(get_db)) -> Collection:
    """Provides access to the 'attachments' collection."""
    return db["attachments"]


def get_audit_logs_collection(db: Database = Depends(get_db)) -> Collection:
    """Provides access to the 'audit_logs' collection."""
    return db["audit_logs"]