# scripts/seed_data.py
#
# Purpose:
#   Populates MongoDB with sample data for the Hospital Support Request
#   System — every entity (User, Category, ServiceRequest, Comment,
#   Attachment, AuditLog) gets at least 8 records, with realistic
#   cross-references (a service request's category_id points to a real
#   category, a comment's request_id points to a real request, etc.), so
#   the API and frontend have something meaningful to show right away.
#
#   Flow modeled: Department Staff raises a request -> Team Lead assigns
#   it to a Support Engineer -> engineer works it (in_progress, possibly
#   on_hold) -> resolves it -> department confirms -> request closed.
#
# This is a one-off maintenance script, not part of the running API, which
# is why it lives in scripts/ instead of app/. It reuses the exact same
# shared MongoDB connection as the app itself (app/database.py) so it
# writes to the same database the API reads from.
#
# Run it from the backend project root with:
#   python -m scripts.seed_data
#
# WARNING: this clears the 6 collections below before inserting, so it's
# meant for a fresh/dev database, not production data.

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Allows running this script directly (python scripts/seed_data.py) by
# putting the project root on the import path, so "from app...." works
# the same way it does for the app itself.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import database  # the same shared connection app/database.py builds

# ---------------------------------------------------------------------------
# IDs are plain, readable strings (not real uuid4 values) on purpose — the
# app's schemas only require "id" to be a string, they never validate uuid
# *format*. Readable ids make it far easier to see how records cross-reference
# each other in this seed file.
# ---------------------------------------------------------------------------

NOW = datetime.utcnow()


def days_ago(n: int) -> datetime:
    """Small helper so seeded timestamps look realistic and spread out."""
    return NOW - timedelta(days=n)


# --- 1. Users (8) — covering all four roles ---------------------------------
# Roles per the spec: department_staff, support_engineer, team_lead, admin
USERS = [
    {"id": "user-dept-1", "name": "Priya Sharma", "email": "priya.sharma@hospital.org",
     "password": "password123", "role": "department_staff", "department": "Radiology", "created_at": days_ago(30)},
    {"id": "user-dept-2", "name": "Rahul Verma", "email": "rahul.verma@hospital.org",
     "password": "password123", "role": "department_staff", "department": "Cardiology", "created_at": days_ago(29)},
    {"id": "user-dept-3", "name": "Ananya Gupta", "email": "ananya.gupta@hospital.org",
     "password": "password123", "role": "department_staff", "department": "Emergency", "created_at": days_ago(28)},
    {"id": "user-dept-4", "name": "Karan Mehta", "email": "karan.mehta@hospital.org",
     "password": "password123", "role": "department_staff", "department": "Pharmacy", "created_at": days_ago(27)},
    {"id": "user-lead-1", "name": "Neha Singh", "email": "neha.singh@hospital.org",
     "password": "password123", "role": "team_lead", "department": "Facilities", "created_at": days_ago(60)},
    {"id": "user-support-1", "name": "Arjun Nair", "email": "arjun.nair@hospital.org",
     "password": "password123", "role": "support_engineer", "department": "Facilities", "created_at": days_ago(50)},
    {"id": "user-support-2", "name": "Divya Iyer", "email": "divya.iyer@hospital.org",
     "password": "password123", "role": "support_engineer", "department": "Facilities", "created_at": days_ago(45)},
    {"id": "user-admin-1", "name": "Vikram Rao", "email": "vikram.rao@hospital.org",
     "password": "password123", "role": "admin", "department": "Administration", "created_at": days_ago(90)},
]

# --- 2. Categories (8, mapped onto the 4 request categories) ----------------
CATEGORIES = [
    {"id": "cat-equip-1", "name": "EQUIPMENT_ISSUE", "description": "Medical equipment malfunction or damage", "created_at": days_ago(90)},
    {"id": "cat-equip-2", "name": "EQUIPMENT_ISSUE", "description": "IT equipment (workstations, scanners) issues", "created_at": days_ago(90)},
    {"id": "cat-maint-1", "name": "MAINTENANCE", "description": "Plumbing, electrical, and HVAC maintenance", "created_at": days_ago(90)},
    {"id": "cat-maint-2", "name": "MAINTENANCE", "description": "Furniture and fixture repairs", "created_at": days_ago(90)},
    {"id": "cat-it-1", "name": "IT_ISSUE", "description": "Network, software, and systems access issues", "created_at": days_ago(90)},
    {"id": "cat-it-2", "name": "IT_ISSUE", "description": "Hospital information system (HIS) issues", "created_at": days_ago(90)},
    {"id": "cat-facility-1", "name": "FACILITY_REQUEST", "description": "Room setup, cleaning, and space requests", "created_at": days_ago(90)},
    {"id": "cat-facility-2", "name": "FACILITY_REQUEST", "description": "Signage, access badges, and general facility requests", "created_at": days_ago(90)},
]

# --- 3. Service Requests (8) — spans every lifecycle status at least once ---
# Lifecycle: NEW -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED
# with the possible detour IN_PROGRESS <-> ON_HOLD
SERVICE_REQUESTS = [
    {"id": "req-1", "title": "MRI machine displaying error code", "description": "Radiology MRI unit shows E-204 and stopped mid-scan.",
     "category_id": "cat-equip-1", "status": "new", "created_by": "user-dept-1", "assigned_to": None,
     "created_at": days_ago(6), "updated_at": days_ago(6)},
    {"id": "req-2", "title": "Cardiology ward AC not cooling", "description": "AC unit in Cardiology ward B runs but blows warm air.",
     "category_id": "cat-maint-1", "status": "assigned", "created_by": "user-dept-2", "assigned_to": "user-support-1",
     "created_at": days_ago(5), "updated_at": days_ago(4)},
    {"id": "req-3", "title": "Cannot access patient records system", "description": "HIS login times out for the entire Emergency team.",
     "category_id": "cat-it-2", "status": "in_progress", "created_by": "user-dept-3", "assigned_to": "user-support-2",
     "created_at": days_ago(5), "updated_at": days_ago(3)},
    {"id": "req-4", "title": "Need refrigeration unit for pharmacy stock", "description": "Additional cold-storage unit required for vaccine overflow.",
     "category_id": "cat-facility-1", "status": "on_hold", "created_by": "user-dept-4", "assigned_to": "user-support-1",
     "created_at": days_ago(4), "updated_at": days_ago(2)},
    {"id": "req-5", "title": "Leaking pipe near Radiology store room", "description": "Steady leak under the sink, floor getting wet.",
     "category_id": "cat-maint-1", "status": "resolved", "created_by": "user-dept-1", "assigned_to": "user-support-2",
     "created_at": days_ago(10), "updated_at": days_ago(1)},
    {"id": "req-6", "title": "Nurse station printer offline", "description": "Printer at Cardiology nurse station not responding to print jobs.",
     "category_id": "cat-it-1", "status": "closed", "created_by": "user-dept-2", "assigned_to": "user-support-1",
     "created_at": days_ago(12), "updated_at": days_ago(1)},
    {"id": "req-7", "title": "Broken chair in Emergency waiting area", "description": "One of the waiting area chairs has a broken leg, safety risk.",
     "category_id": "cat-maint-2", "status": "new", "created_by": "user-dept-3", "assigned_to": None,
     "created_at": days_ago(1), "updated_at": days_ago(1)},
    {"id": "req-8", "title": "New access badge for pharmacy storeroom", "description": "New pharmacy hire needs storeroom access provisioned.",
     "category_id": "cat-facility-2", "status": "assigned", "created_by": "user-dept-4", "assigned_to": "user-support-2",
     "created_at": days_ago(2), "updated_at": days_ago(1)},
]

# --- 4. Comments (8) — spread across several requests -----------------------
COMMENTS = [
    {"id": "comment-1", "request_id": "req-1", "author_id": "user-dept-1",
     "content": "Rebooted the unit as instructed, error code still shows.", "created_at": days_ago(6)},
    {"id": "comment-2", "request_id": "req-2", "author_id": "user-support-1",
     "content": "Checking the compressor now, will update shortly.", "created_at": days_ago(4)},
    {"id": "comment-3", "request_id": "req-2", "author_id": "user-dept-2",
     "content": "Thanks, ward is getting warm quickly.", "created_at": days_ago(4)},
    {"id": "comment-4", "request_id": "req-3", "author_id": "user-support-2",
     "content": "Looking into the HIS authentication server logs now.", "created_at": days_ago(3)},
    {"id": "comment-5", "request_id": "req-4", "author_id": "user-dept-4",
     "content": "Any update on procurement approval for the unit?", "created_at": days_ago(2)},
    {"id": "comment-6", "request_id": "req-5", "author_id": "user-support-2",
     "content": "Pipe replaced and floor dried, please confirm it's fixed.", "created_at": days_ago(1)},
    {"id": "comment-7", "request_id": "req-6", "author_id": "user-dept-2",
     "content": "Confirmed, printer working again. Thank you!", "created_at": days_ago(1)},
    {"id": "comment-8", "request_id": "req-8", "author_id": "user-support-2",
     "content": "Badge provisioned, activating access tomorrow morning.", "created_at": days_ago(1)},
]

# --- 5. Attachments (8) — metadata only, spread across several requests -----
ATTACHMENTS = [
    {"id": "attachment-1", "request_id": "req-1", "uploaded_by": "user-dept-1",
     "filename": "mri_error_screen.png", "url": "https://files.example.com/mri_error_screen.png",
     "size": 204800, "created_at": days_ago(6)},
    {"id": "attachment-2", "request_id": "req-2", "uploaded_by": "user-support-1",
     "filename": "ac_unit_reading.txt", "url": "https://files.example.com/ac_unit_reading.txt",
     "size": 5120, "created_at": days_ago(4)},
    {"id": "attachment-3", "request_id": "req-3", "uploaded_by": "user-dept-3",
     "filename": "his_login_error.png", "url": "https://files.example.com/his_login_error.png",
     "size": 153600, "created_at": days_ago(5)},
    {"id": "attachment-4", "request_id": "req-4", "uploaded_by": "user-dept-4",
     "filename": "procurement_request.pdf", "url": "https://files.example.com/procurement_request.pdf",
     "size": 81920, "created_at": days_ago(4)},
    {"id": "attachment-5", "request_id": "req-5", "uploaded_by": "user-support-2",
     "filename": "pipe_leak_photo.jpg", "url": "https://files.example.com/pipe_leak_photo.jpg",
     "size": 512000, "created_at": days_ago(9)},
    {"id": "attachment-6", "request_id": "req-6", "uploaded_by": "user-dept-2",
     "filename": "printer_error_screenshot.png", "url": "https://files.example.com/printer_error_screenshot.png",
     "size": 174080, "created_at": days_ago(12)},
    {"id": "attachment-7", "request_id": "req-7", "uploaded_by": "user-dept-3",
     "filename": "broken_chair_photo.jpg", "url": "https://files.example.com/broken_chair_photo.jpg",
     "size": 245760, "created_at": days_ago(1)},
    {"id": "attachment-8", "request_id": "req-8", "uploaded_by": "user-support-2",
     "filename": "badge_request_form.pdf", "url": "https://files.example.com/badge_request_form.pdf",
     "size": 92160, "created_at": days_ago(1)},
]

# --- 6. Audit logs (8) — matching real actions taken on the requests above --
AUDIT_LOGS = [
    {"id": "audit-1", "request_id": "req-1", "action": "created", "performed_by": "user-dept-1",
     "details": "Request created with status 'new'.", "created_at": days_ago(6)},
    {"id": "audit-2", "request_id": "req-2", "action": "created", "performed_by": "user-dept-2",
     "details": "Request created with status 'new'.", "created_at": days_ago(5)},
    {"id": "audit-3", "request_id": "req-2", "action": "assigned", "performed_by": "user-lead-1",
     "details": "Assigned to user 'user-support-1'. Status moved from 'new' to 'assigned'.", "created_at": days_ago(4)},
    {"id": "audit-4", "request_id": "req-3", "action": "created", "performed_by": "user-dept-3",
     "details": "Request created with status 'new'.", "created_at": days_ago(5)},
    {"id": "audit-5", "request_id": "req-3", "action": "assigned", "performed_by": "user-lead-1",
     "details": "Assigned to user 'user-support-2'. Status moved from 'new' to 'assigned'.", "created_at": days_ago(4)},
    {"id": "audit-6", "request_id": "req-3", "action": "status_changed", "performed_by": "user-support-2",
     "details": "Status changed from 'assigned' to 'in_progress'.", "created_at": days_ago(3)},
    {"id": "audit-7", "request_id": "req-4", "action": "status_changed", "performed_by": "user-support-1",
     "details": "Status changed from 'in_progress' to 'on_hold' pending procurement approval.", "created_at": days_ago(2)},
    {"id": "audit-8", "request_id": "req-6", "action": "status_changed", "performed_by": "user-dept-2",
     "details": "Status changed from 'resolved' to 'closed'.", "created_at": days_ago(1)},
]


def seed() -> None:
    """Clears the 6 collections and inserts the fixed seed data above."""
    collections_and_data = [
        ("users", USERS),
        ("categories", CATEGORIES),
        ("service_requests", SERVICE_REQUESTS),
        ("comments", COMMENTS),
        ("attachments", ATTACHMENTS),
        ("audit_logs", AUDIT_LOGS),
    ]

    for collection_name, documents in collections_and_data:
        collection = database[collection_name]
        deleted = collection.delete_many({}).deleted_count
        collection.insert_many(documents)
        print(f"{collection_name}: cleared {deleted} old record(s), inserted {len(documents)} new record(s)")


if __name__ == "__main__":
    seed()
    print("\nSeeding complete.")