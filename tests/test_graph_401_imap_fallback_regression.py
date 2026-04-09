from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from outlook_web.services import graph as graph_service
from tests._import_app import clear_login_attempts, import_web_app_module


class Graph401ImapFallbackRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = import_web_app_module()
        cls.app = cls.module.app

    def setUp(self):
        with self.app.app_context():
            clear_login_attempts()

    def _login(self, client):
        resp = client.post("/login", json={"password": "testpass123"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue((resp.get_json() or {}).get("success"))

    def _insert_outlook_account(self, email_addr: str) -> None:
        conn = self.module.create_sqlite_connection()
        try:
            conn.execute(
                """
                INSERT INTO accounts (
                    email, password, client_id, refresh_token, group_id, status,
                    account_type, provider
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (email_addr, "pw", "cid-test", "rt-test", 1, "active", "outlook", "outlook"),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _mock_graph_response(status_code: int, error_code: str):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = {
            "error": {
                "code": error_code,
                "message": "mock graph failure",
            }
        }
        return response

    @patch("outlook_web.services.graph.requests.get")
    @patch("outlook_web.services.graph.get_access_token_graph_result")
    def test_graph_401_access_denied_does_not_mark_auth_expired(self, mock_get_token, mock_get):
        mock_get_token.return_value = {"success": True, "access_token": "graph-token", "refresh_token": None}
        mock_get.return_value = self._mock_graph_response(401, "ErrorAccessDenied")

        result = graph_service.get_emails_graph("cid-test", "rt-test", folder="inbox", skip=0, top=1)

        self.assertFalse(result.get("success"))
        self.assertFalse(result.get("auth_expired"))
        self.assertEqual(result.get("error", {}).get("status"), 401)

    @patch("outlook_web.services.graph.requests.get")
    @patch("outlook_web.services.graph.get_access_token_graph_result")
    def test_graph_401_invalid_auth_token_marks_auth_expired(self, mock_get_token, mock_get):
        mock_get_token.return_value = {"success": True, "access_token": "graph-token", "refresh_token": None}
        mock_get.return_value = self._mock_graph_response(401, "InvalidAuthenticationToken")

        result = graph_service.get_emails_graph("cid-test", "rt-test", folder="inbox", skip=0, top=1)

        self.assertFalse(result.get("success"))
        self.assertTrue(result.get("auth_expired"))
        self.assertEqual(result.get("error", {}).get("status"), 401)

    @patch("outlook_web.controllers.emails.imap_service.get_emails_imap_with_server")
    @patch("outlook_web.controllers.emails.graph_service.get_emails_graph")
    def test_get_emails_falls_back_to_imap_when_graph_401_is_access_denied(self, mock_get_graph, mock_get_imap):
        client = self.app.test_client()
        self._login(client)

        email_addr = "fallback-list@example.com"
        self._insert_outlook_account(email_addr)

        mock_get_graph.return_value = {
            "success": False,
            "auth_expired": False,
            "error": {
                "type": "GraphAPIError",
                "status": 401,
                "code": "EMAIL_FETCH_FAILED",
                "message": "Access is denied",
            },
        }
        mock_get_imap.return_value = {
            "success": True,
            "emails": [
                {
                    "id": "imap-1",
                    "subject": "IMAP Subject",
                    "from": {"emailAddress": {"address": "imap@example.com"}},
                    "receivedDateTime": "2026-04-09T00:00:00Z",
                    "isRead": False,
                    "hasAttachments": False,
                    "bodyPreview": "preview",
                }
            ],
        }

        resp = client.get(f"/api/emails/{email_addr}?folder=inbox&skip=0&top=20")

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json() or {}
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("method"), "IMAP (New)")
        self.assertEqual(len(data.get("emails", [])), 1)

    @patch("outlook_web.services.verification_extractor.extract_verification_info")
    @patch("outlook_web.controllers.emails.get_email_detail_imap_generic_result")
    @patch("outlook_web.controllers.emails.imap_service.get_emails_imap_with_server")
    @patch("outlook_web.controllers.emails.graph_service.get_emails_graph")
    def test_extract_verification_falls_back_to_imap_when_graph_401_is_access_denied(
        self,
        mock_get_graph,
        mock_get_imap,
        mock_get_detail,
        mock_extract,
    ):
        client = self.app.test_client()
        self._login(client)

        email_addr = "fallback-extract@example.com"
        self._insert_outlook_account(email_addr)

        mock_get_graph.side_effect = [
            {
                "success": False,
                "auth_expired": False,
                "error": {"type": "GraphAPIError", "status": 401, "code": "EMAIL_FETCH_FAILED"},
            },
            {
                "success": False,
                "auth_expired": False,
                "error": {"type": "GraphAPIError", "status": 401, "code": "EMAIL_FETCH_FAILED"},
            },
        ]
        mock_get_imap.return_value = {
            "success": True,
            "emails": [
                {
                    "id": "imap-1",
                    "subject": "Verification code",
                    "from": "imap@example.com",
                    "date": "2026-04-09T00:00:00Z",
                    "is_read": False,
                    "has_attachments": False,
                    "body_preview": "Your code is 123456",
                }
            ],
        }
        mock_get_detail.return_value = {
            "success": True,
            "email": {
                "subject": "Verification code",
                "body_text": "Your code is 123456",
                "body_html": "",
            },
        }
        mock_extract.return_value = {"verification_code": "123456", "links": [], "formatted": "123456"}

        resp = client.get(f"/api/emails/{email_addr}/extract-verification")

        self.assertEqual(resp.status_code, 200)
        data = resp.get_json() or {}
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("data", {}).get("verification_code"), "123456")
        self.assertEqual(mock_get_imap.call_count, 2)
