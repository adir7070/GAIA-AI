"""Security primitives: password hashing, JWT, AES-256-GCM, HMAC."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ----- Passwords -----------------------------------------------------------
def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


# ----- JWT -----------------------------------------------------------------
def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=settings.JWT_EXPIRE_HOURS)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except JWTError as e:
        raise ValueError(f"invalid token: {e}") from e


# ----- AES-256-GCM at-rest encryption --------------------------------------
def _aes_key_bytes() -> bytes:
    raw = settings.AES_KEY
    if not raw:
        raise RuntimeError("AES_KEY is not configured")
    try:
        key = base64.b64decode(raw)
    except Exception:
        key = raw.encode("utf-8")
    if len(key) not in (16, 24, 32):
        # Derive a 32-byte key deterministically if the env value is not raw key bytes.
        key = hashlib.sha256(key).digest()
    return key


def encrypt_text(plaintext: str, aad: bytes | None = None) -> str:
    """Encrypt with AES-256-GCM. Returns base64(nonce||ciphertext||tag)."""
    if plaintext is None:
        return ""
    key = _aes_key_bytes()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), aad)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt_text(blob: str, aad: bytes | None = None) -> str:
    if not blob:
        return ""
    key = _aes_key_bytes()
    aesgcm = AESGCM(key)
    raw = base64.b64decode(blob)
    nonce, ct = raw[:12], raw[12:]
    return aesgcm.decrypt(nonce, ct, aad).decode("utf-8")


# ----- HMAC for bridge webhook ---------------------------------------------
def hmac_sign(payload: bytes, secret: str | None = None) -> str:
    s = (secret or settings.BRIDGE_SECRET).encode("utf-8")
    return hmac.new(s, payload, hashlib.sha256).hexdigest()


def hmac_verify(payload: bytes, signature: str, secret: str | None = None) -> bool:
    expected = hmac_sign(payload, secret)
    return hmac.compare_digest(expected, signature)
