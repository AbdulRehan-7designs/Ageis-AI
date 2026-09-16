import os
import sys
import unittest
from fastapi.testclient import TestClient

# Support relative import of backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.auth import create_access_token
from app.services.ingestion import ingestion_service

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestChatRBACIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Ingest 4 clearance tier document fixtures into Qdrant before tests run."""
        fixtures = [
            ("sample_public.pdf", "Public Safety Manual", "PUBLIC"),
            ("sample_internal.pdf", "Internal Facility Guide", "INTERNAL"),
            ("sample_restricted.pdf", "Restricted Defense Directive", "RESTRICTED"),
            ("sample_secret.pdf", "Secret Sovereign Protocol", "SECRET"),
        ]
        for filename, doc_name, tag in fixtures:
            path = os.path.join(BASE_DIR, "test_data", filename)
            if os.path.exists(path):
                ingestion_service.ingest_pdf(
                    pdf_path=path,
                    doc_name=doc_name,
                    classification_tag=tag,
                )

    def test_chat_public_user_cannot_see_restricted_or_secret_citations(self):
        """Verify POST /api/v1/chat as PUBLIC clearance user excludes RESTRICTED & SECRET docs."""
        client = TestClient(app)
        
        # Generate JWT for PUBLIC user
        public_token = create_access_token(
            data={
                "sub": "test_public_user",
                "role": "PUBLIC",
                "clearance_tags": ["PUBLIC"],
            }
        )
        
        headers = {"Authorization": f"Bearer {public_token}"}
        payload = {"message": "defense clearance guidelines and operational workflow"}
        
        response = client.post("/api/v1/chat", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200, f"Expected 200 OK, got {response.status_code}: {response.text}")
        
        data = response.json()
        citations = data.get("citations", [])
        returned_tags = {c["tag"] for c in citations}
        
        # Assert PUBLIC user ONLY receives PUBLIC tags
        self.assertTrue(returned_tags.issubset({"PUBLIC"}), f"Security Failure! PUBLIC user received unauthorized citations: {returned_tags}")
        self.assertNotIn("RESTRICTED", returned_tags, "RESTRICTED doc leaked to PUBLIC user!")
        self.assertNotIn("SECRET", returned_tags, "SECRET doc leaked to PUBLIC user!")
        print(f"\n[PASS] PUBLIC User Chat Integration Test Passed. Citations returned: {returned_tags}")

    def test_chat_secret_user_retrieves_all_clearance_levels(self):
        """Verify POST /api/v1/chat as SECRET clearance user retrieves all clearance levels."""
        client = TestClient(app)
        
        # Generate JWT for ADMIN / SECRET user
        secret_token = create_access_token(
            data={
                "sub": "test_secret_user",
                "role": "ADMIN",
                "clearance_tags": ["PUBLIC", "INTERNAL", "RESTRICTED", "SECRET"],
            }
        )
        
        headers = {"Authorization": f"Bearer {secret_token}"}
        payload = {"message": "defense clearance guidelines and operational workflow"}
        
        response = client.post("/api/v1/chat", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200, f"Expected 200 OK, got {response.status_code}: {response.text}")
        
        data = response.json()
        citations = data.get("citations", [])
        returned_tags = {c["tag"] for c in citations}
        
        # Assert SECRET user receives RESTRICTED and SECRET tags
        self.assertTrue("SECRET" in returned_tags or "RESTRICTED" in returned_tags, f"SECRET user failed to retrieve restricted/secret content! Tags: {returned_tags}")
        print(f"\n[PASS] SECRET User Chat Integration Test Passed. Citations returned: {returned_tags}")

if __name__ == "__main__":
    unittest.main()
