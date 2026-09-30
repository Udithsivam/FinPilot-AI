import datetime as dt

import jwt
import pytest

from backend.app.core.config import get_settings
from backend.app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_and_verify_roundtrip():
    hashed = hash_password("supersecret123")
    assert hashed != "supersecret123"
    assert verify_password("supersecret123", hashed) is True


def test_verify_rejects_wrong_password():
    hashed = hash_password("supersecret123")
    assert verify_password("wrongpassword", hashed) is False


def test_verify_rejects_overlong_password_without_crashing():
    hashed = hash_password("supersecret123")
    assert verify_password("x" * 100, hashed) is False


def test_hash_of_overlong_password_raises():
    # UserCreate caps password length at 72 before this is ever called; this
    # documents that hash_password itself has no such guard, unlike verify_password.
    with pytest.raises(ValueError):
        hash_password("x" * 100)


def test_access_token_roundtrip():
    token = create_access_token(subject="user@example.com")
    assert decode_access_token(token) == "user@example.com"


def test_decode_rejects_garbage_token():
    assert decode_access_token("not-a-real-token") is None


def test_decode_rejects_expired_token():
    settings = get_settings()
    expired_payload = {
        "sub": "user@example.com",
        "exp": dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1),
    }
    expired_token = jwt.encode(expired_payload, settings.secret_key, algorithm=settings.algorithm)
    assert decode_access_token(expired_token) is None


def test_decode_rejects_token_signed_with_wrong_key():
    settings = get_settings()
    payload = {"sub": "user@example.com", "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5)}
    forged_token = jwt.encode(payload, "a-completely-different-signing-key-value", algorithm=settings.algorithm)
    assert decode_access_token(forged_token) is None
