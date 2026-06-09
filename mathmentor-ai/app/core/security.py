"""Authentication and input-safety helpers."""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import Settings, get_settings


class AuthenticationError(ValueError):
    """Raised when token validation or credential verification fails."""


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(
    subject: str,
    settings: Settings | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT access token."""
    resolved = settings or get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=resolved.access_token_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expires_at, "type": "access"}
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(
        payload,
        resolved.secret_key.get_secret_value(),
        algorithm=resolved.algorithm,
    )


def create_refresh_token(
    subject: str,
    settings: Settings | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT refresh token."""
    resolved = settings or get_settings()
    expires_at = datetime.now(UTC) + timedelta(days=resolved.refresh_token_expire_days)
    payload: dict[str, Any] = {"sub": subject, "exp": expires_at, "type": "refresh"}
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(
        payload,
        resolved.secret_key.get_secret_value(),
        algorithm=resolved.algorithm,
    )


def decode_access_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    """Decode and validate an access token."""
    resolved = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            resolved.secret_key.get_secret_value(),
            algorithms=[resolved.algorithm],
        )
    except JWTError as exc:
        raise AuthenticationError("Invalid access token.") from exc
    if payload.get("type") != "access" or not payload.get("sub"):
        raise AuthenticationError("Invalid access token claims.")
    return payload


def decode_refresh_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    """Decode and validate a refresh token."""
    resolved = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            resolved.secret_key.get_secret_value(),
            algorithms=[resolved.algorithm],
        )
    except JWTError as exc:
        raise AuthenticationError("Invalid refresh token.") from exc
    if payload.get("type") != "refresh" or not payload.get("sub"):
        raise AuthenticationError("Invalid refresh token claims.")
    return payload
