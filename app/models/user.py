from enum import Enum

class UserRole(str,Enum):
    DEPARTMENT_STAFF = "department_staff"
    SUPPORT_ENGINEER = "support_engineer"
    TEAM_LEAD = "team_lead"
    ADMIN = "admin"