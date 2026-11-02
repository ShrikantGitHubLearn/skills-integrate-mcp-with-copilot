import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path


TEACHERS_FILE = Path(
    os.environ.get("TEACHERS_FILE", str(Path(__file__).with_name("teachers.json")))
)
SESSION_COOKIE_NAME = "teacher_session"
SESSION_MAX_AGE = 60 * 60 * 12
SESSION_SECRET = os.environ.get("SESSION_SECRET")
SESSION_SIGNING_KEY = (
    SESSION_SECRET.encode("utf-8") if SESSION_SECRET else secrets.token_bytes(32)
)


def hash_password(password: str) -> dict[str, str]:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32
    )
    return {"salt": salt.hex(), "password_hash": password_hash.hex()}


def verify_password(password: str, record: dict[str, str]) -> bool:
    try:
        salt = bytes.fromhex(record["salt"])
        expected_hash = bytes.fromhex(record["password_hash"])
        actual_hash = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32
        )
    except (KeyError, TypeError, ValueError):
        return False
    return hmac.compare_digest(actual_hash, expected_hash)


def load_teachers() -> dict[str, dict[str, str]]:
    try:
        data = json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Teacher credentials must be a JSON object")
    return data


def create_session_token(username: str) -> str:
    expires_at = int(time.time()) + SESSION_MAX_AGE
    payload = f"{username}\n{expires_at}".encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
    signature = hmac.new(
        SESSION_SIGNING_KEY, encoded_payload.encode("ascii"), hashlib.sha256
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def get_session_username(token: str | None) -> str | None:
    if not token:
        return None
    try:
        encoded_payload, signature = token.rsplit(".", 1)
        expected_signature = hmac.new(
            SESSION_SIGNING_KEY, encoded_payload.encode("ascii"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None
        padding = "=" * (-len(encoded_payload) % 4)
        payload = base64.urlsafe_b64decode(encoded_payload + padding).decode("utf-8")
        username, expires_at = payload.rsplit("\n", 1)
        if int(expires_at) <= int(time.time()):
            return None
    except (ValueError, UnicodeDecodeError):
        return None
    return username