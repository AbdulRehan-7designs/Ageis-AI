import os
import sys
import unittest
from fastapi.testclient import TestClient

# Support relative import of backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.auth import create_access_token
from app.services.sandbox import sandbox_service


class TestSovereignSandbox(unittest.TestCase):

    def test_safe_python_execution(self):
        """Test executing valid mathematical / telemetry code in sandbox."""
        code = """
vibration_values = [4.2, 4.5, 4.8, 5.1, 5.4]
avg = sum(vibration_values) / len(vibration_values)
print(f"Average Vibration: {avg:.2f} mm/s")
"""
        result = sandbox_service.execute(code)
        self.assertEqual(result.status, "SUCCESS")
        self.assertIn("Average Vibration: 4.80 mm/s", result.stdout)
        self.assertEqual(len(result.violations), 0)

    def test_blocked_dangerous_imports(self):
        """Test AST static analyzer blocks forbidden modules like os, subprocess, socket."""
        dangerous_codes = [
            "import os; os.system('echo HACKED')",
            "import subprocess; subprocess.run(['ls'])",
            "import socket; s = socket.socket()",
            "from os import path",
            "eval('1 + 1')",
        ]

        for code in dangerous_codes:
            result = sandbox_service.execute(code)
            self.assertEqual(result.status, "SECURITY_VIOLATION", f"Failed to block: {code}")
            self.assertTrue(len(result.violations) > 0)
            print(f"[PASS] Blocked dangerous snippet '{code[:30]}...': {result.violations}")

    def test_sandbox_timeout_enforcement(self):
        """Test sandbox kills process when execution exceeds timeout limit."""
        infinite_loop = """
import time
while True:
    pass
"""
        result = sandbox_service.execute(infinite_loop, timeout_sec=1.0)
        self.assertEqual(result.status, "TIMEOUT")
        self.assertIn("Execution timed out", result.stderr)

    def test_sandbox_api_endpoint(self):
        """Test POST /api/v1/sandbox/execute via FastAPI TestClient."""
        client = TestClient(app)
        token = create_access_token(data={"sub": "engineer_user", "role": "ENGINEER", "clearance_tags": ["INTERNAL"]})
        headers = {"Authorization": f"Bearer {token}"}

        payload = {"code": "print('Telemetry calculation complete.')"}
        response = client.post("/api/v1/sandbox/execute", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["stdout"], "Telemetry calculation complete.")


if __name__ == "__main__":
    unittest.main()
