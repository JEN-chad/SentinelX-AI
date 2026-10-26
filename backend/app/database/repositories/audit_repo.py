"""SentinelX AI - Append-Only Audit Log Repository"""

from datetime import datetime, timezone
import hashlib
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import AuditLogRecord


class AuditRepository:
    """Repository handling append-only audit logging with cryptographic verification hashes."""

    @staticmethod
    def log(
        db: Session,
        actor: str,
        operation: str,
        entity_id: str,
        status: str,
        details: str,
    ) -> AuditLogRecord:
        """Append an audit record with deterministic sha256 verification hash."""
        now = datetime.now(timezone.utc)
        audit_id = f"aud-{now.strftime('%Y%m%d%H%M%S%f')[-10:]}"

        hash_payload = f"{audit_id}:{actor}:{operation}:{entity_id}:{status}:{now.isoformat()}"
        verification_hash = f"sha256:{hashlib.sha256(hash_payload.encode('utf-8')).hexdigest()[:24]}"

        record = AuditLogRecord(
            audit_id=audit_id,
            timestamp=now,
            actor=actor,
            operation=operation,
            entity_id=entity_id,
            status=status,
            details=details,
            verification_hash=verification_hash,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def list_logs(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        entity_id: Optional[str] = None,
    ) -> List[AuditLogRecord]:
        stmt = select(AuditLogRecord)
        if entity_id:
            stmt = stmt.where(AuditLogRecord.entity_id == entity_id)
        stmt = stmt.order_by(AuditLogRecord.timestamp.desc()).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())
