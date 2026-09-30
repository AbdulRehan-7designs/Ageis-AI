import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.egress_guard import EgressBlockedError, EgressGuard, install_httpx_hooks
import httpx


class TestEgressGuard(unittest.TestCase):
    def setUp(self):
        self.guard = EgressGuard()

    def test_allows_localhost_and_docker_ollama(self):
        local = self.guard.evaluate("http://127.0.0.1:11434/api/tags")
        docker = self.guard.evaluate("http://ollama:11434/api/generate")
        qdrant = self.guard.evaluate("http://qdrant:6333/readyz")
        self.assertTrue(local.allowed)
        self.assertTrue(docker.allowed)
        self.assertTrue(qdrant.allowed)
        self.assertEqual(local.classification, "INTERNAL")

    def test_blocks_cloud_llm_and_cdn(self):
        openai = self.guard.evaluate("https://api.openai.com/v1/chat/completions")
        unpkg = self.guard.evaluate("https://unpkg.com/pdfjs-dist/build/pdf.worker.min.mjs")
        self.assertFalse(openai.allowed)
        self.assertFalse(unpkg.allowed)
        self.assertEqual(openai.classification, "EXTERNAL")

    def test_records_block_counts(self):
        self.guard.reset()
        self.guard.record(self.guard.evaluate("https://api.anthropic.com/v1/messages"))
        snap = self.guard.snapshot()
        self.assertEqual(snap["blocked_count"], 1)
        self.assertEqual(snap["events"][0]["host"], "api.anthropic.com")
        self.assertIn("AIR_GAP", snap["sovereign_status"])

    def test_httpx_hook_blocks_external(self):
        install_httpx_hooks()
        with self.assertRaises(EgressBlockedError):
            with httpx.Client(timeout=1.0) as client:
                client.get("https://example.com/")


if __name__ == "__main__":
    unittest.main()
