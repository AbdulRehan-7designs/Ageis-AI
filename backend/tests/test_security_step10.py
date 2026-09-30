from datetime import timedelta

from fastapi.testclient import TestClient

from app.core.auth import create_access_token
from app.core.config import settings
from app.main import app
from app.services.audit_service import audit_service


client = TestClient(app)


def auth_headers(username="engineer", role="ENGINEER", clearance=None, expires_delta=None):
    token = create_access_token(
        data={
            "sub": username,
            "role": role,
            "clearance_tags": clearance or ["SECRET"],
        },
        expires_delta=expires_delta,
    )
    return {"Authorization": f"Bearer {token}"}


def setup_function():
    audit_service.clear()


def test_audit_requires_authentication_and_scopes_normal_users():
    assert client.get("/api/v1/audit/logs").status_code == 401

    audit_service.log_entry(
        event_type="TEST",
        username="engineer",
        clearance_tags=["INTERNAL"],
        query_or_action="owned",
        equipment_tag="P-1",
        status="OK",
    )
    audit_service.log_entry(
        event_type="TEST",
        username="other-user",
        clearance_tags=["INTERNAL"],
        query_or_action="other",
        equipment_tag="P-2",
        status="OK",
    )
    response = client.get("/api/v1/audit/logs", headers=auth_headers(clearance=["SECRET"]))
    assert response.status_code == 200
    assert [entry["username"] for entry in response.json()] == ["engineer"]


def test_audit_verification_requires_auditor_or_admin():
    assert client.get("/api/v1/audit/verify").status_code == 401
    assert client.get(
        "/api/v1/audit/verify",
        headers=auth_headers(role="OPERATOR", clearance=["INTERNAL"]),
    ).status_code == 403
    assert client.get(
        "/api/v1/audit/verify",
        headers=auth_headers(username="auditor", role="AUDITOR", clearance=["INTERNAL"]),
    ).status_code == 200


def test_hitl_requires_reviewer_and_uses_server_identity():
    payload = {
        "action_id": "ACT-1",
        "equipment_tag": "P-101",
        "approved_by": "attacker",
    }
    assert client.post("/api/v1/hitl/approve", json=payload).status_code == 401
    assert client.post(
        "/api/v1/hitl/approve",
        json=payload,
        headers=auth_headers(username="operator", role="OPERATOR", clearance=["INTERNAL"]),
    ).status_code == 403

    response = client.post(
        "/api/v1/hitl/approve",
        json=payload,
        headers=auth_headers(username="real-reviewer", role="ENGINEER", clearance=["INTERNAL"]),
    )
    assert response.status_code == 200
    assert response.json()["approved_by"] == "real-reviewer"
    assert audit_service.get_logs()[-1]["username"] == "real-reviewer"


def test_client_clearance_claim_does_not_expand_development_identity():
    response = client.post(
        "/api/v1/hitl/approve",
        json={"action_id": "ACT-2", "equipment_tag": "P-102", "approved_by": "attacker"},
        headers=auth_headers(
            username="engineer",
            role="ENGINEER",
            clearance=["SECRET"],
        ),
    )
    assert response.status_code == 200
    assert "SECRET" not in response.json()["clearance_tags"]


def test_legacy_maintenance_report_requires_authentication():
    payload = {
        "asset": "P-204",
        "issue_summary": "Elevated vibration",
        "evidence_blocks": [{"classification": "INTERNAL", "snippet": "Observed"}],
        "generated_by": "attacker",
        "classification_level": "SECRET",
    }
    assert client.post("/api/v1/reports/maintenance", json=payload).status_code == 401


def test_expired_token_is_rejected():
    response = client.get(
        "/api/v1/audit/logs",
        headers=auth_headers(expires_delta=timedelta(seconds=-1)),
    )
    assert response.status_code == 401


def test_development_identity_fallback_is_rejected_outside_development(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "ALLOW_DEVELOPMENT_IDENTITY_FALLBACK", True)
    response = client.get("/api/v1/audit/logs", headers=auth_headers())
    assert response.status_code == 401
