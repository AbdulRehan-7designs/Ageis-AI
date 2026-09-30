import os
import sys
import json
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.models import Base, UserRecord
from app.db.repository import (
    _hash_password,
    bootstrap_users,
    find_user,
    list_runs,
    save_run,
    verify_password,
)
from app.services.agent_orchestrator import AgentOrchestrator, AgentPlan, AgentRun, AgentStep


def test_password_hash_verification_does_not_store_plaintext():
    encoded = _hash_password("correct horse battery staple")
    assert "correct horse battery staple" not in encoded
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong password", encoded)


def test_bootstrap_provisions_persistent_identity_without_client_role_control(monkeypatch, tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'users.db'}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    monkeypatch.setenv(
        "AEGIS_BOOTSTRAP_USERS_JSON",
        json.dumps([{"username": "admin", "password": "first-secret", "role": "ADMIN"}]),
    )
    with sessions() as db:
        bootstrap_users(db)
        user = find_user(db, "admin")
        assert user is not None
        assert verify_password("first-secret", user.password_hash)
        assert user.role == "ADMIN"
        assert "RESTRICTED" in user.clearance_tags

    monkeypatch.setenv(
        "AEGIS_BOOTSTRAP_USERS_JSON",
        json.dumps([{"username": "admin", "password": "second-secret", "role": "OPERATOR"}]),
    )
    with sessions() as db:
        bootstrap_users(db)
        user = find_user(db, "admin")
        assert user.role == "OPERATOR"
        assert verify_password("second-secret", user.password_hash)
        assert not verify_password("first-secret", user.password_hash)


def test_agent_run_persists_and_is_scoped_to_user(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'agent-runs.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = UserRecord(
            username="operator",
            password_hash=_hash_password("secret"),
            role="OPERATOR",
            clearance_tags=["PUBLIC", "INTERNAL"],
        )
        other = UserRecord(
            username="other",
            password_hash=_hash_password("secret"),
            role="OPERATOR",
            clearance_tags=["PUBLIC"],
        )
        db.add_all([user, other])
        db.commit()
        db.refresh(user)
        db.refresh(other)

        save_run(
            db,
            {
                "run_id": "run-1",
                "task": "Inspect pump evidence",
                "model_id": "local",
                "status": "COMPLETED",
                "steps": [{"tool": "document_search", "status": "COMPLETED"}],
            },
            user,
        )

        assert len(list_runs(db, user)) == 1
        assert list_runs(db, other) == []
        assert find_user(db, "operator").role == "OPERATOR"

    # Recreate the session and read the same run after the original service
    # context has been discarded.
    with Session(engine) as restarted_db:
        assert list_runs(restarted_db, user)[0]["status"] == "COMPLETED"


def test_agent_run_lifecycle_is_persisted_across_reinitialized_sessions(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'lifecycle.db'}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        user = UserRecord(
            username="operator",
            password_hash=_hash_password("secret"),
            role="OPERATOR",
            clearance_tags=["INTERNAL"],
        )
        db.add(user)
        db.commit()

    run = AgentRun(
        run_id="lifecycle-1",
        user_id="operator",
        task="calculate 5 + 7",
        task_type="analysis",
        model_id="chat",
    )
    plan = AgentPlan(
        plan_id="plan-lifecycle-1",
        task=run.task,
        steps=[AgentStep(id="step-1", description="Calculate", tool="calculator", arguments={"expression": "5 + 7"})],
    )
    with patch("app.db.session.SessionLocal", sessions):
        AgentOrchestrator.execute_plan(plan, run, user_clearance=["INTERNAL"], username="operator")

    with sessions() as db:
        persisted = list_runs(db, db.get(UserRecord, 1))[0]
        assert persisted["run_id"] == "lifecycle-1"
        assert persisted["status"] == "COMPLETED"
        assert persisted["steps"][0]["status"] == "COMPLETED"
