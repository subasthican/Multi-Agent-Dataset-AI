import unittest
from unittest.mock import patch

from starlette.requests import Request
from security.client_ip import client_ip


class ClientIPTests(unittest.TestCase):
    def request(self, value):
        return Request({"type": "http", "headers": [(b"x-forwarded-for", value.encode())], "client": ("127.0.0.1", 1234)})

    def test_local_deployment_ignores_spoofed_header(self):
        with patch.dict("os.environ", {"VERCEL": "0"}):
            self.assertEqual(client_ip(self.request("203.0.113.5")), "127.0.0.1")

    def test_vercel_uses_platform_client_ip(self):
        with patch.dict("os.environ", {"VERCEL": "1"}):
            self.assertEqual(client_ip(self.request("203.0.113.5")), "203.0.113.5")

    def test_missing_invalid_or_ambiguous_header_falls_back(self):
        with patch.dict("os.environ", {"VERCEL": "1"}):
            for value in ("", "invalid", "203.0.113.5, 203.0.113.6"):
                self.assertEqual(client_ip(self.request(value)), "127.0.0.1")

    def test_ipv6_subject_is_normalized(self):
        with patch.dict("os.environ", {"VERCEL": "1"}):
            self.assertEqual(client_ip(self.request("2001:0db8::1")), "2001:db8::1")
