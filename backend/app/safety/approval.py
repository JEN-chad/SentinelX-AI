"""SentinelX AI - Human-In-The-Loop Approval Workflow

Manages human security analyst reviews and sign-offs for disruptive defensive responses.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.common import ActionType, ApprovalStatus


class ApprovalRecord(BaseModel):
    """Structured record of human approval decision."""
    approval_id: str
    incident_id: str
    action: ActionType
    reviewer_id: str
    status: ApprovalStatus
    comment: Optional[str] = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApprovalWorkflow:
    """Manages approval state checks and records analyst decisions."""

    @staticmethod
    def create_approval(
        incident_id: str,
        action: ActionType,
        reviewer_id: str,
        status: ApprovalStatus = ApprovalStatus.APPROVED,
        comment: Optional[str] = None,
    ) -> ApprovalRecord:
        """Record an analyst approval decision."""
        now = datetime.now(timezone.utc)
        approval_id = f"appr-{now.strftime('%Y%m%d%H%M%S%f')[-8:]}"

        return ApprovalRecord(
            approval_id=approval_id,
            incident_id=incident_id,
            action=action,
            reviewer_id=reviewer_id,
            status=status,
            comment=comment or "Approved via Security Dashboard",
            decided_at=now,
        )
