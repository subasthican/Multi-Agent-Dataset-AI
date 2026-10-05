import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from google.genai.errors import ClientError, ServerError
from llm import gemini_client as gemini


def quota_error(delay="120s", daily=True):
    return ClientError(429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "details": [
        {"violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier" if daily else "GenerateRequestsPerMinute"}]},
        {"retryDelay": delay}]}})


class GeminiCooldownTests(unittest.TestCase):
    def setUp(self):
        gemini._cooldowns.clear()
        self.env = patch.dict(os.environ, {"GEMINI_API_KEY": "synthetic-only", "GEMINI_MODEL": "synthetic-model"})
        self.env.start()
        self.client = Mock()
        self.binding = patch.object(gemini, "get_client", return_value=self.client)
        self.binding.start()

    def tearDown(self):
        self.binding.stop()
        self.env.stop()
        gemini._cooldowns.clear()

    def test_daily_failure_prevents_repeated_remote_calls(self):
        self.client.models.generate_content.side_effect = quota_error()
        with patch.object(gemini.time, "monotonic", return_value=100):
            for _ in range(3):
                with self.assertRaises(gemini.LLMUnavailableError) as error:
                    gemini.generate_response("test")
                self.assertEqual(error.exception.reason, "DAILY_QUOTA")
                self.assertEqual(error.exception.retry_after_seconds, 120)
        self.assertEqual(self.client.models.generate_content.call_count, 1)

    def test_attempted_flag_distinguishes_provider_error_from_cached_denial(self):
        self.client.models.generate_content.side_effect = quota_error()
        for attempted in (True, False):
            with self.assertRaises(gemini.LLMUnavailableError) as error: gemini.generate_response("test")
            self.assertEqual(error.exception.provider_attempted, attempted)

    def test_probe_resumes_after_retry_delay(self):
        self.client.models.generate_content.side_effect = [quota_error("2s"), SimpleNamespace(text="valid")]
        with patch.object(gemini.time, "monotonic", return_value=100):
            with self.assertRaises(gemini.LLMUnavailableError): gemini.generate_response("first")
        with patch.object(gemini.time, "monotonic", return_value=102):
            self.assertEqual(gemini.generate_response("second"), "valid")
        self.assertEqual(self.client.models.generate_content.call_count, 2)

    def test_model_and_credential_cooldowns_are_separate(self):
        self.client.models.generate_content.side_effect = [quota_error(), SimpleNamespace(text="model two"), SimpleNamespace(text="key two")]
        with self.assertRaises(gemini.LLMUnavailableError): gemini.generate_response("first")
        with patch.dict(os.environ, {"GEMINI_MODEL": "different-model"}):
            self.assertEqual(gemini.generate_response("second"), "model two")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "different-synthetic-key"}):
            self.assertEqual(gemini.generate_response("third"), "key two")

    def test_daily_missing_delay_uses_bounded_probe_backoff(self):
        reason, delay = gemini._provider_cooldown(quota_error("invalid"))
        self.assertEqual((reason, delay), ("DAILY_QUOTA", 3600))

    def test_explicit_sixty_second_daily_delay_is_honored(self):
        self.assertEqual(gemini._provider_cooldown(quota_error("60s")), ("DAILY_QUOTA", 60))

    def test_fractional_delay_rounds_up(self):
        self.assertEqual(gemini._provider_cooldown(quota_error("1.5s", daily=False)), ("RATE_LIMIT", 2))

    def test_service_unavailable_uses_short_cooldown(self):
        self.client.models.generate_content.side_effect = ServerError(503, {"error": {"status": "UNAVAILABLE"}})
        for _ in range(2):
            with self.assertRaises(gemini.LLMUnavailableError) as error: gemini.generate_response("test")
            self.assertEqual(error.exception.reason, "TEMPORARY_UNAVAILABLE")
        self.assertEqual(self.client.models.generate_content.call_count, 1)

    def test_other_failure_and_empty_response_do_not_claim_success(self):
        self.client.models.generate_content.side_effect = [ValueError("network unavailable"), SimpleNamespace(text="")]
        for _ in range(2):
            with self.assertRaises(gemini.LLMUnavailableError): gemini.generate_response("test")
        self.assertEqual(gemini._cooldowns, {})

    def test_malformed_provider_details_do_not_break_fallback(self):
        self.assertEqual(gemini._provider_cooldown(ClientError(429, {"error": {"details": [{"violations": None}]}})), ("RATE_LIMIT", 60))


class ClientConfigurationTests(unittest.TestCase):
    def test_key_rotation_replaces_client_and_retries_are_bounded(self):
        gemini._client_for_key.cache_clear()
        try:
            with patch.object(gemini.genai, "Client") as factory:
                with patch.dict(os.environ, {"GEMINI_API_KEY": "synthetic-key-one"}):
                    gemini.get_client(); gemini.get_client()
                self.assertEqual(factory.call_count, 1)
                options = factory.call_args.kwargs["http_options"]
                self.assertEqual(options.timeout, 30_000)
                self.assertEqual(options.retry_options.attempts, 1)
                with patch.dict(os.environ, {"GEMINI_API_KEY": "synthetic-key-two"}):
                    gemini.get_client()
                self.assertEqual(factory.call_count, 2)
        finally:
            gemini._client_for_key.cache_clear()
