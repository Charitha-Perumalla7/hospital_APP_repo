# This file is the "entry point" of the application
from fastapi import FastAPI

from app.config import settings
from app.database import ping_database
from app.routers import users
from app.routers import categories
from app.routers import service_requests
from app.routers import comments
from app.routers import attachments
from app.routers import audit_logs

# Creating FastAPI app instance
app = FastAPI(title=settings.APP_NAME)

app.include_router(users.router)
app.include_router(categories.router)
app.include_router(service_requests.router)
app.include_router(comments.router)
app.include_router(attachments.router)
app.include_router(audit_logs.router)


def on_startup() -> None:
    if not ping_database():
        raise RuntimeError("Could not connect to MongoDB")
    print(f"[startup]Connected to MongoDB. App:{settings.APP_NAME}")

# Checks basic health-check API endpoint & confirms 
# GET / is running & reachable. (/ is considered as 'root')
@app.get("/",tags=["Health"])
def health_check():
    return {"status":"ok","app":settings.APP_NAME}