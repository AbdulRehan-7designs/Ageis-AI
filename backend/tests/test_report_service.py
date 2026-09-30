import hashlib
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.report_service import ReportService


class TestReportService(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.service = ReportService(self.directory.name)
        self.spec = {
            "title": "P-204 Evidence Report",
            "asset": "P-204",
            "classification": "INTERNAL",
            "executive_summary": "Evidence summary.",
            "findings": ["Vibration was recorded."],
            "evidence": [{
                "document_id": "doc-1",
                "document_name": "maintenance.pdf",
                "page": 2,
                "source_type": "MAINTENANCE_REPORT",
                "extraction_method": "TEXT",
                "engineering_tags": ["P-204"],
                "classification": "INTERNAL",
                "retrieval_reason": "TAG_MATCH",
                "snippet": "Vibration recorded during inspection.",
            }],
            "recommended_verification": "Inspect recorded parameters.",
        }

    def tearDown(self):
        self.directory.cleanup()

    def test_all_formats_are_local_and_hashed(self):
        expected_headers = {
            "DOCX": b"PK",
            "XLSX": b"PK",
            "PPTX": b"PK",
            "PDF": b"%PDF",
        }
        for report_format, header in expected_headers.items():
            result = self.service.generate({**self.spec, "format": report_format}, "engineer", ["INTERNAL"])
            content = open(result["path"], "rb").read()
            self.assertTrue(content.startswith(header))
            self.assertEqual(result["content_hash"], hashlib.sha256(content).hexdigest())
            self.assertEqual(result["status"], "REVIEW_REQUIRED")

    def test_unauthorized_evidence_is_rejected(self):
        with self.assertRaises(PermissionError):
            self.service.generate({**self.spec, "format": "PDF", "evidence": [{**self.spec["evidence"][0], "classification": "SECRET"}]}, "operator", ["INTERNAL"])

    def test_storage_name_is_generated(self):
        result = self.service.generate({**self.spec, "format": "PDF"}, "engineer", ["INTERNAL"])
        self.assertNotIn("..", result["storage_name"])
        self.assertTrue(result["storage_name"].startswith("ART-"))


if __name__ == "__main__":
    unittest.main()
