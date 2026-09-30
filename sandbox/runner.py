import json
import os
import subprocess
import sys
import tempfile
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

MAX_OUTPUT = int(os.environ.get("SANDBOX_MAX_OUTPUT_BYTES", "65536"))
MAX_INPUT = int(os.environ.get("SANDBOX_MAX_INPUT_BYTES", "32768"))


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/execute":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_INPUT:
            self._write({"status": "INPUT_REJECTED", "stderr": "Input exceeds sandbox limit."}, 413)
            return
        request = json.loads(self.rfile.read(length))
        code = str(request.get("code") or "")
        started = time.monotonic()
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir="/tmp") as script:
            script.write("inputs = " + repr(request.get("inputs") or {}) + "\n")
            script.write(code)
            path = script.name
        try:
            process = subprocess.Popen(
                [sys.executable, "-I", "-B", path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                env={"PYTHONNOUSERSITE": "1", "PATH": "/usr/local/bin:/usr/bin:/bin"},
            )
            try:
                stdout, stderr = process.communicate(timeout=min(float(request.get("timeout_sec") or 5), 30))
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                self._write(self._result("TIMEOUT", request, started, stdout, "Execution timed out."))
                return
            status = "COMPLETED" if process.returncode == 0 else "FAILED"
            self._write(self._result(status, request, started, stdout, stderr))
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    def _result(self, status, request, started, stdout="", stderr=""):
        stdout = (stdout or "")[:MAX_OUTPUT]
        stderr = (stderr or "")[:MAX_OUTPUT]
        elapsed = time.monotonic() - started
        return {
            "status": status,
            "stdout": stdout,
            "stderr": stderr,
            "result": stdout.strip() if status == "COMPLETED" else None,
            "execution_time_sec": round(elapsed, 4),
            "execution_time_ms": int(elapsed * 1000),
            "violations": [],
            "sandbox_id": request.get("sandbox_id", ""),
            "network_enabled": False,
            "code_hash": "",
        }

    def _write(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
