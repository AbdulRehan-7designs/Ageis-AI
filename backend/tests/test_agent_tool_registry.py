import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agent_orchestrator import AgentOrchestrator, AgentPlan, AgentRun, AgentStep
from app.services.tool_registry import ToolRegistry, tool_registry


class TestToolRegistry(unittest.TestCase):
    def test_register_and_list_tools(self):
        registry = ToolRegistry()
        self.assertIn("document_search", {tool.name for tool in registry.list_tools()})
        self.assertIn("calculator", {tool.name for tool in registry.list_tools()})

    def test_retrieve_tool_and_validate_arguments(self):
        tool = tool_registry.get("document_search")
        self.assertIsNotNone(tool)
        self.assertEqual(tool.risk_level.value, "READ_ONLY")
        self.assertEqual(tool.validate_arguments({"query": "vibration limit"})["query"], "vibration limit")

    def test_disabled_tool_rejected(self):
        tool = tool_registry.get("document_search")
        tool.enabled = False
        try:
            with self.assertRaises(ValueError):
                tool_registry.validate("document_search", {"query": "hello"})
        finally:
            tool.enabled = True

    def test_unknown_tool_rejected(self):
        with self.assertRaises(KeyError):
            tool_registry.validate("unknown_tool", {"query": "hello"})

    def test_invalid_arguments_rejected(self):
        with self.assertRaises(ValueError):
            tool_registry.validate("calculator", {"expression": ""})

    def test_document_search_uses_authorized_rag(self):
        with patch("app.services.tool_registry.rag_service.build_rag_context") as mocked_search:
            mocked_search.return_value = {
                "citations": [
                    {
                        "document_name": "SOP-017",
                        "page": 12,
                        "section_title": "Vibration Limits",
                        "tag": "INTERNAL",
                        "snippet": "P-204 vibration limit is 4.0 mm/s.",
                        "score": 0.92,
                    }
                ],
                "context_text": "P-204 vibration limit is 4.0 mm/s.",
                "result_count": 1,
            }
            result = tool_registry.execute("document_search", {"query": "P-204 vibration limit"}, user_clearance=["INTERNAL"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["document"], "SOP-017")

    def test_calculator_executes_safely(self):
        result = tool_registry.execute("calculator", {"expression": "(10 + 2) * 3 / 2"})
        self.assertEqual(result["result"], 18.0)

    def test_document_read_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            tool_registry.execute("document_read", {"doc_name": "../../etc/passwd"})

    def test_document_read_reads_safe_document(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = Path(tmpdir) / "approved.txt"
            doc_path.write_text("The approved limit is 4.0 mm/s.", encoding="utf-8")
            with patch("app.services.tool_registry._ALLOWED_DOCUMENT_ROOT", Path(tmpdir)):
                result = tool_registry.execute("document_read", {"stored_filename": "approved.txt", "max_chars": 100})
            self.assertIn("approved limit", result["content_preview"])


class TestAgentPlannerAndExecutor(unittest.TestCase):
    def test_build_valid_plan(self):
        plan = AgentOrchestrator.build_plan("Investigate vibration for P-204 and calculate the percentage increase.")
        self.assertEqual(plan.steps[0].tool, "document_search")
        self.assertTrue(any(step.tool == "calculator" for step in plan.steps))

    def test_unknown_tool_rejected_by_validator(self):
        plan = AgentPlan(
            plan_id="plan-1",
            task="test task",
            steps=[AgentStep(id="step-1", description="invalid", tool="not_a_real_tool", arguments={"query": "hello"})],
        )
        with self.assertRaises(ValueError):
            AgentOrchestrator.validate_plan(plan)

    def test_malformed_step_rejected(self):
        plan = AgentPlan(
            plan_id="plan-2",
            task="test task",
            steps=[AgentStep(id="step-1", description="invalid", tool="document_search", arguments={})],
        )
        with self.assertRaises(ValueError):
            AgentOrchestrator.validate_plan(plan)

    def test_execute_calculator_plan(self):
        run = AgentRun(
            run_id="run-1",
            user_id="operator",
            task="calculate 5 + 7",
            task_type="analysis",
            model_id="chat",
        )
        plan = AgentPlan(
            plan_id="plan-3",
            task="calculate 5 + 7",
            steps=[AgentStep(id="step-1", description="Calculate expression", tool="calculator", arguments={"expression": "5 + 7"})],
        )
        result = AgentOrchestrator.execute_plan(plan, run, user_clearance=["INTERNAL"], username="operator")
        self.assertEqual(result["tool_results"][0]["result"], 12)
        self.assertEqual(run.status, "COMPLETED")

    def test_agent_run_state_transitions(self):
        run = AgentRun(
            run_id="run-2",
            user_id="operator",
            task="Investigate P-204 vibration",
            task_type="maintenance",
            model_id="chat",
        )
        plan = AgentOrchestrator.build_plan("Investigate P-204 vibration")
        with patch("app.services.tool_registry.rag_service.build_rag_context") as mocked_search:
            mocked_search.return_value = {
                "citations": [{"document_name": "SOP-017", "page": 22, "section_title": "Limits", "tag": "INTERNAL", "snippet": "P-204 limit is 4.0 mm/s.", "score": 0.9}],
                "context_text": "P-204 limit is 4.0 mm/s.",
                "result_count": 1,
            }
            result = AgentOrchestrator.execute_plan(plan, run, user_clearance=["INTERNAL"], username="operator")
        self.assertEqual(result["summary"], "Plan executed successfully using approved, allow-listed tools.")
        self.assertEqual(run.status, "COMPLETED")


if __name__ == "__main__":
    unittest.main()
