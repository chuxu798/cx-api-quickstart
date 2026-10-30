"""Offline SDK transport tests. No .env files, real keys, or network requests."""

import json
from contextlib import redirect_stderr
import io
import logging
import unittest
from unittest.mock import patch

import httpx

from chat import ChatError, ConfigurationError, chat, create_client, load_config, main

FAKE_KEY = "test-key-not-a-secret"
TEST_ENV = {
    "CX_API_KEY": FAKE_KEY,
    "CX_MODEL": "test-model",
    "CX_BASE_URL": "https://cx-api.invalid/v1",
}


def completion(content="模拟回复"):
    return {
        "id": "chatcmpl-mock",
        "object": "chat.completion",
        "created": 0,
        "model": "test-model",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
    }


class ChatTests(unittest.TestCase):
    def setUp(self):
        # Defense in depth: even an accidental real HTTPX transport is blocked.
        self.network_guard = patch(
            "httpx.HTTPTransport.handle_request",
            side_effect=AssertionError("Real network requests are forbidden in tests"),
        )
        self.network_guard.start()
        self.addCleanup(self.network_guard.stop)
        self.config = load_config(TEST_ENV)

    def client(self, handler):
        transport = httpx.MockTransport(handler)
        client = create_client(self.config, httpx.Client(transport=transport))
        self.addCleanup(client.close)
        return client

    def test_request_and_text_response(self):
        requests = []

        def handler(request):
            requests.append(request)
            self.assertEqual(request.method, "POST")
            self.assertEqual(str(request.url), "https://cx-api.invalid/v1/chat/completions")
            self.assertEqual(request.headers["authorization"], f"Bearer {FAKE_KEY}")
            self.assertEqual(json.loads(request.content), {
                "model": "test-model",
                "messages": [{"role": "user", "content": "你好"}],
            })
            self.assertEqual(request.extensions["timeout"]["read"], 30.0)
            return httpx.Response(200, json=completion())

        self.assertEqual(chat(self.client(handler), self.config.model, "你好"), "模拟回复")
        self.assertEqual(len(requests), 1)

    def test_http_errors_are_safe_and_never_retried(self):
        for status in (401, 403, 404, 429, 500):
            with self.subTest(status=status):
                calls = []

                def handler(request):
                    calls.append(request)
                    return httpx.Response(status, json={"error": {"message": FAKE_KEY}})

                with self.assertRaises(ChatError) as caught:
                    chat(self.client(handler), self.config.model, "hello")
                self.assertIn(str(status), str(caught.exception))
                self.assertNotIn(FAKE_KEY, str(caught.exception))
                self.assertEqual(len(calls), 1)

    def test_timeout_is_safe_and_never_retried(self):
        calls = []

        def handler(request):
            calls.append(request)
            raise httpx.ReadTimeout(FAKE_KEY, request=request)

        with self.assertRaisesRegex(ChatError, "超时"):
            chat(self.client(handler), self.config.model, "hello")
        self.assertEqual(len(calls), 1)

    def test_connection_error(self):
        def handler(request):
            raise httpx.ConnectError(FAKE_KEY, request=request)

        with self.assertRaisesRegex(ChatError, "无法连接"):
            chat(self.client(handler), self.config.model, "hello")

    def test_empty_response(self):
        payloads = [completion(None), completion(""), completion("   ")]
        payloads.append({**completion(), "choices": []})
        for payload in payloads:
            with self.subTest(payload=payload):
                client = self.client(lambda request: httpx.Response(200, json=payload))
                with self.assertRaisesRegex(ChatError, "未包含文本"):
                    chat(client, self.config.model, "hello")

    def test_empty_prompt_sends_no_request(self):
        def handler(request):
            self.fail("An empty prompt must not send a request")

        with self.assertRaises(ConfigurationError):
            chat(self.client(handler), self.config.model, "  ")

    def test_config_validation(self):
        invalid_envs = [
            {},
            {"CX_API_KEY": FAKE_KEY},
            {**TEST_ENV, "CX_API_KEY": "your-cx-api-key"},
            {**TEST_ENV, "CX_API_KEY": "key with spaces"},
            {**TEST_ENV, "CX_MODEL": " "},
        ]
        for base_url in (
            "", "http://cx-api.invalid/v1", "https://user:pass@cx-api.invalid/v1",
            "https://cx-api.invalid/v1?key=secret", "https://cx-api.invalid/v1#part",
            "https:///v1", "https://cx-api.invalid:bad/v1", "https://cx api.invalid/v1",
        ):
            invalid_envs.append({**TEST_ENV, "CX_BASE_URL": base_url})
        for env in invalid_envs:
            with self.subTest(env=env):
                with self.assertRaises(ConfigurationError):
                    load_config(env)

    def test_defaults_and_secret_safe_repr(self):
        config = load_config({"CX_API_KEY": FAKE_KEY, "CX_MODEL": "test-model"})
        self.assertEqual(config.base_url, "https://api.www-cx-api.cn.mt/v1")
        self.assertNotIn(FAKE_KEY, repr(config))

    def test_unrelated_openai_environment_is_not_inherited(self):
        with patch("os.environ", {
            "OPENAI_API_KEY": "unrelated-fake-key",
            "OPENAI_ORG_ID": "unrelated-fake-org",
            "OPENAI_PROJECT_ID": "unrelated-fake-project",
            "OPENAI_WEBHOOK_SECRET": "unrelated-fake-webhook",
        }):
            def handler(request):
                self.assertEqual(request.headers["authorization"], f"Bearer {FAKE_KEY}")
                self.assertNotIn("openai-organization", request.headers)
                self.assertNotIn("openai-project", request.headers)
                return httpx.Response(200, json=completion())

            client = self.client(handler)
            self.assertEqual(client.webhook_secret, "")
            self.assertEqual(chat(client, self.config.model, "hello"), "模拟回复")

    def test_cli_suppresses_sdk_debug_logs_and_raw_errors(self):
        from openai._utils._logs import setup_logging

        output = io.StringIO()
        families = ("openai", "httpx", "httpcore")
        names = set(families) | {
            name for name in logging.Logger.manager.loggerDict
            if any(name.startswith(family + ".") for family in families)
        }
        states = {
            name: (logger.disabled, logger.level, logger.propagate, logger.handlers[:])
            for name in names
            for logger in [logging.getLogger(name)]
        }
        self.addCleanup(self.restore_loggers, states)
        for name in names:
            logger = logging.getLogger(name)
            logger.disabled = False
            logger.setLevel(logging.DEBUG)
            logger.handlers = [logging.StreamHandler(output)]
        with patch("os.environ", {"OPENAI_LOG": "debug"}):
            setup_logging()

        def handler(request):
            for name in ("openai._base_client", "httpx", "httpcore.connection"):
                logging.getLogger(name).debug("unsafe-debug-marker %s", FAKE_KEY)
            return httpx.Response(401, json={"error": {"message": FAKE_KEY}})

        client = self.client(handler)
        with patch("chat.load_config", return_value=self.config), \
                patch("chat.create_client", return_value=client), \
                patch("sys.argv", ["chat.py", "hello"]), redirect_stderr(output):
            self.assertEqual(main(), 1)
        self.assertIn("HTTP 401", output.getvalue())
        self.assertNotIn(FAKE_KEY, output.getvalue())
        self.assertNotIn("unsafe-debug-marker", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    @staticmethod
    def restore_loggers(states):
        for name, (disabled, level, propagate, handlers) in states.items():
            logger = logging.getLogger(name)
            logger.disabled = disabled
            logger.setLevel(level)
            logger.propagate = propagate
            logger.handlers = handlers


if __name__ == "__main__":
    unittest.main()
