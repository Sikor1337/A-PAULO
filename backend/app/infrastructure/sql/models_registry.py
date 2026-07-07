from app.modules.attachments.models.attachment import Attachment
from app.modules.audit.models import AuditEvent
from app.modules.bug_reports.models import BugReport
from app.modules.calendar.models import CalendarAudit, CalendarEvent, CalendarFeedToken
from app.modules.core_data.models.user import User
from app.modules.departments.models import Department, DepartmentMember
from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.models.function import Function
from app.modules.pi.models.group import BeneficiaryAssignment, Group
from app.modules.pi.models.volunteer import Volunteer
from app.modules.recruitment.models import (
    DepartureField,
    DepartureInterview,
    RecruitmentField,
    RecruitmentOnboardingMeeting,
    RecruitmentSubmission,
)
from app.modules.security.models import Permission, UserGroup
from app.modules.tasks.models import Task, TaskAssignee, TaskChecklistItem

__all__ = [
    "Attachment",
    "AuditEvent",
    "Beneficiary",
    "BeneficiaryAssignment",
    "BugReport",
    "CalendarAudit",
    "CalendarEvent",
    "CalendarFeedToken",
    "Department",
    "DepartmentMember",
    "DepartureField",
    "DepartureInterview",
    "Function",
    "Group",
    "Permission",
    "RecruitmentField",
    "RecruitmentOnboardingMeeting",
    "RecruitmentSubmission",
    "Task",
    "TaskAssignee",
    "TaskChecklistItem",
    "User",
    "UserGroup",
    "Volunteer",
]
