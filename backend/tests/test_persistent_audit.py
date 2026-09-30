import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.models import Base
from app.services.audit_service import AuditService


def test_audit_event_survives_service_reinitialization(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'audit.db'}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)

    first_service = AuditService(session_factory=sessions)
    first_service.log_entry(
        event_type="AGENT_RUN_CREATED",
        username="operator",
        clearance_tags=["INTERNAL"],
        query_or_action="run-1",
        status="PLANNING",
    )

    restarted_service = AuditService(session_factory=sessions)
    records = restarted_service.get_logs()
    assert len(records) == 1
    assert records[0]["event_type"] == "AGENT_RUN_CREATED"
    assert restarted_service.verify_audit_chain()["is_valid"]
