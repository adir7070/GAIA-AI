"""Quick unit tests for security primitives (no external services needed)."""
import os

os.environ.setdefault("AES_KEY", "test-key-not-secure-only-for-unit-tests")
os.environ.setdefault("JWT_SECRET", "unit-test-secret")
os.environ.setdefault("BRIDGE_SECRET", "unit-test-bridge")

from app.core.security import (  # noqa: E402
    create_access_token,
    decode_access_token,
    decrypt_text,
    encrypt_text,
    hash_password,
    hmac_sign,
    hmac_verify,
    verify_password,
)


def test_password_roundtrip():
    h = hash_password("hunter2!!")
    assert verify_password("hunter2!!", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip():
    tok = create_access_token(123, extra={"role": "user"})
    data = decode_access_token(tok)
    assert data["sub"] == "123"
    assert data["role"] == "user"


def test_aes_roundtrip():
    msg = "שלום מה קורה?"
    blob = encrypt_text(msg)
    assert blob != msg
    assert decrypt_text(blob) == msg


def test_hmac_roundtrip():
    body = b"some-payload"
    sig = hmac_sign(body)
    assert hmac_verify(body, sig)
    assert not hmac_verify(b"tampered", sig)
