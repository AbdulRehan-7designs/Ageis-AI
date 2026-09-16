import os
import sys
import unittest
from fastapi.testclient import TestClient

# Support relative import of backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.auth import create_access_token
from app.services.audit_service import audit_service


class TestTamperEvidentAuditChain(unittest.TestCase):

    def setUp(self):
        """Reset the audit store before each test."""
        audit_service.clear()

    def test_audit_chain_tamper_detection(self):
        """Test full audit workflow:
        (a) Writes several audit entries via normal chat requests.
        (b) Confirms verify_audit_chain() passes cleanly.
        (c) Manually mutates one stored entry's content directly in storage.
        (d) Confirms verify_audit_chain() correctly detects and reports the chain break.
        """
        client = TestClient(app)

        # Generate access token for test user
        token = create_access_token(
            data={"sub": "operator_test_user", "role": "ENGINEER", "clearance_tags": ["PUBLIC", "INTERNAL"]}
        )
        headers = {"Authorization": f"Bearer {token}"}

        queries = [
            "What is the status of pump P-101 vibration levels?",
            "Check temperature threshold for turbine T-202",
            "Emergency isolation procedure for valve V-303",
        ]

        # Step (a): Send several chat requests
        print("\n=== STEP A: Sending normal chat requests to generate audit log entries ===")
        for i, q in enumerate(queries, start=1):
            response = client.post("/api/v1/chat", json={"message": q}, headers=headers)
            self.assertEqual(response.status_code, 200, f"Request {i} failed: {response.text}")

        # Also add a HITL approval request
        hitl_resp = client.post(
            "/api/v1/hitl/approve",
            json={"action_id": "ACT-999", "equipment_tag": "P-101", "approved_by": "operator_test_user"},
        )
        self.assertEqual(hitl_resp.status_code, 200)

        logs = audit_service.get_logs()
        self.assertEqual(len(logs), 4, f"Expected 4 audit records, got {len(logs)}")
        print(f"Logged {len(logs)} audit entries successfully.")

        # Step (b): Confirm verify_audit_chain() passes
        print("\n=== STEP B: Verifying audit chain before tampering ===")
        verification_1 = audit_service.verify_audit_chain()
        print(f"Verification Result: {verification_1}")
        self.assertTrue(verification_1["is_valid"], "Initial chain verification failed!")
        self.assertIsNone(verification_1["broken_index"], "broken_index should be None for valid chain")

        # Confirm via endpoint GET /api/v1/audit/verify
        endpoint_resp = client.get("/api/v1/audit/verify")
        self.assertEqual(endpoint_resp.status_code, 200)
        self.assertTrue(endpoint_resp.json()["is_valid"])

        # Step (c): Manually mutate one stored entry's content directly in storage
        print("\n=== STEP C: Manually mutating entry #1 query content in storage ===")
        tampered_index = 1
        tampered_entry_id = audit_service.store[tampered_index]["id"]
        original_query = audit_service.store[tampered_index]["query_or_action"]
        audit_service.store[tampered_index]["query_or_action"] = "UNAUTHORIZED TAMPERED QUERY CONTENT"
        print(f"Mutated entry [{tampered_entry_id}] query from '{original_query}' to 'UNAUTHORIZED TAMPERED QUERY CONTENT'")

        # Step (d): Confirm verify_audit_chain() detects and reports the break
        print("\n=== STEP D: Verifying audit chain AFTER tampering ===")
        verification_2 = audit_service.verify_audit_chain()
        print(f"Verification Result After Tampering: {verification_2}")
        self.assertFalse(verification_2["is_valid"], "Chain verification failed to detect tampering!")
        self.assertEqual(verification_2["broken_index"], tampered_index, f"Expected broken_index={tampered_index}, got {verification_2['broken_index']}")
        self.assertEqual(verification_2["broken_entry_id"], tampered_entry_id)
        self.assertIn("Content tamper detected", verification_2["reason"])

        # Verify endpoint also reports the tamper break
        endpoint_tamper_resp = client.get("/api/v1/audit/verify")
        self.assertEqual(endpoint_tamper_resp.status_code, 200)
        data = endpoint_tamper_resp.json()
        self.assertFalse(data["is_valid"])
        self.assertEqual(data["broken_index"], tampered_index)
        print(f"[PASS] Tamper Detection Test Passed! Correctly reported break at index {tampered_index} ({tampered_entry_id})")


if __name__ == "__main__":
    unittest.main()
