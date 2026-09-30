from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from fastapi.testclient import TestClient

from app.core.auth import create_access_token
from app.main import app
from app.db.models import Base, UserRecord
from app.db.repository import (
    _hash_password,
    append_message,
    create_conversation,
    find_conversation,
    list_conversations,
    list_messages,
)


def test_conversations_and_messages_persist_and_are_owner_scoped(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'conversations.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        owner = UserRecord(
            username="alice",
            password_hash=_hash_password("secret"),
            role="ENGINEER",
            clearance_tags=["INTERNAL"],
        )
        other = UserRecord(
            username="bob",
            password_hash=_hash_password("secret"),
            role="ENGINEER",
            clearance_tags=["INTERNAL"],
        )
        db.add_all([owner, other])
        db.commit()
        db.refresh(owner)
        db.refresh(other)

        conversation = create_conversation(db, owner.username, owner.id)
        append_message(db, find_conversation(db, conversation["conversation_id"], "alice"), "USER", "Question")
        append_message(
            db,
            find_conversation(db, conversation["conversation_id"], "alice"),
            "ASSISTANT",
            "Grounded answer",
            agent_run_id="run-1",
            metadata={"citations": [{"document": "procedure.pdf", "page": 4}]},
        )

        assert len(list_conversations(db, "alice")) == 1
        assert list_conversations(db, "bob") == []
        assert find_conversation(db, conversation["conversation_id"], "bob") is None
        messages = list_messages(db, conversation["conversation_id"])
        assert [message["role"] for message in messages] == ["USER", "ASSISTANT"]
        assert messages[1]["metadata"]["citations"][0]["page"] == 4


def test_conversation_owner_cannot_be_changed_by_message_payload(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'ownership.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        conversation = create_conversation(db, "alice", None)
        assert find_conversation(db, conversation["conversation_id"], "bob") is None
        assert find_conversation(db, conversation["conversation_id"], "alice").owner_username == "alice"


def test_conversation_api_requires_auth_and_enforces_owner():
    client = TestClient(app)
    assert client.get("/api/v1/conversations").status_code == 401

    alice_headers = {
        "Authorization": f"Bearer {create_access_token(data={'sub': 'conversation-alice', 'role': 'ENGINEER'})}"
    }
    bob_headers = {
        "Authorization": f"Bearer {create_access_token(data={'sub': 'conversation-bob', 'role': 'ENGINEER'})}"
    }
    created = client.post("/api/v1/conversations", headers=alice_headers, json={"title": "Private"})
    assert created.status_code == 200
    conversation_id = created.json()["conversation_id"]

    assert client.get(f"/api/v1/conversations/{conversation_id}", headers=bob_headers).status_code == 404
    assert client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=bob_headers,
        json={"content": "unauthorized"},
    ).status_code == 404
    assert client.get(f"/api/v1/conversations/{conversation_id}", headers=alice_headers).status_code == 200


def test_chat_persists_user_and_completed_assistant_messages(monkeypatch):
    async def fake_process_query(**kwargs):
        return {
            "diagnosis_summary": "Grounded maintenance answer.",
            "citations": [{"document": "SOP-017", "page": 4}],
            "evidence_blocks": [{"document_name": "SOP-017", "page": 4}],
            "evidence_state": "grounded",
            "agent_run": {"run_id": "run-conversation-test"},
        }

    monkeypatch.setattr("app.api.v1.endpoints.chat.agent_orchestrator.process_query", fake_process_query)
    client = TestClient(app)
    headers = {
        "Authorization": f"Bearer {create_access_token(data={'sub': 'chat-persist-user', 'role': 'ENGINEER'})}"
    }
    created = client.post("/api/v1/conversations", headers=headers, json={})
    conversation_id = created.json()["conversation_id"]

    response = client.post(
        "/api/v1/chat",
        headers=headers,
        json={"conversation_id": conversation_id, "message": "What is the vibration procedure?"},
    )
    assert response.status_code == 200
    restored = client.get(f"/api/v1/conversations/{conversation_id}", headers=headers).json()
    assert [message["role"] for message in restored["messages"]] == ["USER", "ASSISTANT"]
    assert restored["messages"][1]["metadata"]["citations"][0]["page"] == 4
