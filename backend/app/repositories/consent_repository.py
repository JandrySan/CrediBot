from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consent_record import ConsentRecord


class ConsentRepository:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        customer_id: int,
        conversation_id: int,
        consent_type: str,
        status: str,
        purpose: str,
        notice_version: str = "2026-01",
        legal_basis: str = "CONSENT",
        evidence_hash: str | None = None,
    ) -> ConsentRecord:
        now = datetime.now(UTC)
        record = ConsentRecord(
            customer_id=customer_id,
            conversation_id=conversation_id,
            consent_type=consent_type,
            purpose=purpose,
            notice_version=notice_version,
            legal_basis=legal_basis,
            status=status,
            channel="WHATSAPP",
            evidence_hash=evidence_hash,
            granted_at=now if status == "GRANTED" else None,
            revoked_at=now if status == "REVOKED" else None,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def latest_status(self, customer_id: int, consent_type: str) -> str | None:
        return self.db.scalar(
            select(ConsentRecord.status)
            .where(
                ConsentRecord.customer_id == customer_id,
                ConsentRecord.consent_type == consent_type,
            )
            .order_by(ConsentRecord.id.desc())
        )

    def is_granted(self, customer_id: int, consent_type: str) -> bool:
        return self.latest_status(customer_id, consent_type) == "GRANTED"
