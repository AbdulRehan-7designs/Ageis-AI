import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.model_registry import ModelCapability, ModelProviderError, ModelRegistry, model_registry
from app.services.model_router import model_router
from app.services.query_router import query_router


class TestModelRegistry(unittest.TestCase):
    def test_catalog_loads_3b_defaults(self):
        enabled = {m.id: m for m in model_registry.list_models()}
        self.assertIn("chat", enabled)
        self.assertIn("coder", enabled)
        self.assertNotIn("vision", enabled)
        self.assertEqual(enabled["chat"].ollama_tag, "qwen2.5:3b")
        self.assertEqual(enabled["coder"].ollama_tag, "qwen2.5-coder:3b")

    def test_capability_lookup(self):
        coding_models = model_registry.find_by_capability(ModelCapability.CODING)
        self.assertTrue(any(model.id == "coder" for model in coding_models))
        chat_models = model_registry.find_by_capability("chat")
        self.assertTrue(any(model.id == "chat" for model in chat_models))

    def test_invalid_model_id_raises(self):
        self.assertIsNone(model_registry.get("not-a-real-model"))
        with self.assertRaises(KeyError):
            model_registry.get_provider("not-a-real-model")

    def test_disabled_model_is_excluded(self):
        self.assertNotIn("vision", {model.id for model in model_registry.list_models()})
        self.assertEqual([], model_registry.find_by_capability("vision"))

    def test_auto_selects_coder_for_code_task(self):
        selection = model_registry.select(
            "Write a python script in the sandbox to calculate RUL"
        )
        self.assertTrue(selection.auto_selected)
        self.assertEqual(selection.task_type, "code")
        self.assertEqual(selection.ollama_tag, "qwen2.5-coder:3b")

    def test_auto_selects_chat_for_document_summary(self):
        selection = model_registry.select(
            "Summarize the inspection findings and draft an approval note"
        )
        self.assertEqual(selection.task_type, "document_summary")
        self.assertEqual(selection.ollama_tag, "qwen2.5:3b")

    def test_vision_falls_back_to_chat_while_disabled(self):
        selection = model_registry.select("Read this scanned P&ID drawing and locate PSV-204")
        self.assertEqual(selection.task_type, "vision")
        self.assertEqual(selection.ollama_tag, "qwen2.5:3b")
        self.assertIn("no enabled specialist", selection.reason)

    def test_manual_override_wins(self):
        selection = model_registry.select("hello", override="qwen2.5-coder:3b")
        self.assertFalse(selection.auto_selected)
        self.assertEqual(selection.ollama_tag, "qwen2.5-coder:3b")

    def test_auto_override_token_is_ignored(self):
        selection = model_registry.select("summarize SOP-017", override="auto")
        self.assertTrue(selection.auto_selected)
        self.assertEqual(selection.ollama_tag, "qwen2.5:3b")

    def test_ollama_health_reports_unavailable_when_server_missing(self):
        registry = ModelRegistry()
        with patch("app.services.model_registry.httpx.AsyncClient") as mocked_client:
            mocked_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=httpx.ConnectError("offline"))
            health = registry.health_check("chat")
            self.assertEqual(health["status"], "UNAVAILABLE")

    def test_registry_generate_text_uses_provider_abstraction(self):
        async def _fake_generate(*args, **kwargs):
            return "Grounded answer from model registry"

        with patch.object(model_registry, "get_provider") as mocked_get_provider:
            provider = mock_provider = unittest.mock.Mock()
            mock_provider.generate = AsyncMock(return_value="Grounded answer from model registry")
            mocked_get_provider.return_value = provider
            result = model_registry.resolve_model("chat")
            self.assertIsNotNone(result)

            import asyncio
            async_result = asyncio.run(
                model_registry.generate_text(
                    model_id_or_tag="chat",
                    prompt="What is the maintenance plan?",
                    system="system prompt",
                    options={"temperature": 0.1},
                    timeout=15.0,
                )
            )
            self.assertEqual(async_result, "Grounded answer from model registry")
            mock_provider.generate.assert_awaited_once()

    def test_provider_error_for_empty_model_response(self):
        provider = model_registry.get_provider("chat")
        with patch("app.services.model_registry.httpx.AsyncClient") as mocked_client:
            response = unittest.mock.Mock(status_code=200)
            response.json.return_value = {"response": ""}
            mocked_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=response)
            with self.assertRaises(ModelProviderError):
                import asyncio
                asyncio.run(provider.generate(model="qwen2.5:3b", prompt="hello", timeout=15.0))


class TestModelRouter(unittest.TestCase):
    def test_router_routes_code_queries_to_coder(self):
        selection = model_router.route_query("Write a python script to calculate RUL")
        self.assertEqual(selection.task_type, "code")
        self.assertEqual(selection.model_id, "coder")
        self.assertTrue(selection.auto_selected)

    def test_router_routes_document_queries_to_chat(self):
        selection = model_router.route_query("Summarize the approved maintenance note")
        self.assertEqual(selection.task_type, "maintenance")
        self.assertEqual(selection.model_id, "chat")

    def test_router_respects_manual_override(self):
        selection = model_router.route_query("hello there", override="qwen2.5-coder:3b")
        self.assertFalse(selection.auto_selected)
        self.assertEqual(selection.model_id, "coder")
        self.assertEqual(selection.ollama_tag, "qwen2.5-coder:3b")


class TestQueryRouter(unittest.TestCase):
    def test_empty_query(self):
        route = query_router.route("")
        self.assertEqual(route["intent"], "unknown")

    def test_drawing_where_query_does_not_crash(self):
        route = query_router.route("Where is PSV-204 on the P&ID drawing?")
        self.assertEqual(route["intent"], "drawing")
        self.assertIn("PSV-204", route["expanded_query"])
        self.assertEqual(route["identifiers"], ["PSV-204"])
        self.assertTrue(route["keywords"])

    def test_maintenance_query(self):
        route = query_router.route("vibration maintenance inspection repair")
        self.assertEqual(route["intent"], "maintenance")


if __name__ == "__main__":
    unittest.main()
