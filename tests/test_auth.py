import json
import tempfile
import unittest
from http.cookies import SimpleCookie
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException, Request, Response

from src import app, auth


def make_request(cookie: str | None = None) -> Request:
    headers = [(b"host", b"testserver")]
    if cookie:
        headers.append((b"cookie", f"{auth.SESSION_COOKIE_NAME}={cookie}".encode()))
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": headers,
        "server": ("testserver", 80),
        "client": ("testclient", 12345),
        "root_path": "",
    }
    return Request(scope)


class TeacherAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.credentials_path = Path(self.temp_dir.name) / "teachers.json"
        self.path_patch = patch.object(auth, "TEACHERS_FILE", self.credentials_path)
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)
        self.addCleanup(self.temp_dir.cleanup)

    def test_password_hash_verifies_without_storing_plaintext(self) -> None:
        record = auth.hash_password("correct-horse-battery")
        self.assertNotIn("password", record)
        self.assertTrue(auth.verify_password("correct-horse-battery", record))
        self.assertFalse(auth.verify_password("incorrect-password", record))

    def test_unauthenticated_users_can_read_but_not_mutate(self) -> None:
        self.assertIn("Chess Club", app.get_activities())
        with self.assertRaises(HTTPException) as signup_error:
            app.signup_for_activity("Chess Club", "new-student@mergington.edu", make_request())
        self.assertEqual(signup_error.exception.status_code, 401)
        with self.assertRaises(HTTPException) as unregister_error:
            app.unregister_from_activity(
                "Chess Club", "michael@mergington.edu", make_request()
            )
        self.assertEqual(unregister_error.exception.status_code, 401)

    def test_valid_teacher_can_sign_up_and_unregister(self) -> None:
        password = "correct-horse-battery"
        self.credentials_path.write_text(
            json.dumps({"teacher1": auth.hash_password(password)}), encoding="utf-8"
        )
        response = Response()
        result = app.login(
            app.LoginRequest(username="teacher1", password=password),
            make_request(),
            response,
        )
        self.assertTrue(result["authenticated"])

        cookie = SimpleCookie()
        cookie.load(response.headers["set-cookie"])
        session_token = cookie[auth.SESSION_COOKIE_NAME].value
        request = make_request(session_token)

        email = "auth-test@mergington.edu"
        self.assertIn("Signed up", app.signup_for_activity("Chess Club", email, request)["message"])
        self.assertIn(email, app.activities["Chess Club"]["participants"])
        self.assertIn(
            "Unregistered",
            app.unregister_from_activity("Chess Club", email, request)["message"],
        )


if __name__ == "__main__":
    unittest.main()