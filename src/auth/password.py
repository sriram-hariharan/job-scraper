from __future__ import annotations

import bcrypt

from src.config.consts import (
    AUTH_BCRYPT_ROUNDS,
    AUTH_PASSWORD_MAX_BYTES,
    AUTH_PASSWORD_MIN_LENGTH,
)


def _password_text(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Password must be a string.")
    return value


def validate_new_password(password: str) -> None:
    raw = _password_text(password)

    if not raw:
        raise ValueError("Password is required.")

    if not raw.strip():
        raise ValueError("Password cannot be blank.")

    if len(raw) < AUTH_PASSWORD_MIN_LENGTH:
        raise ValueError(
            f"Password must be at least {AUTH_PASSWORD_MIN_LENGTH} characters."
        )

    encoded = raw.encode("utf-8")
    if len(encoded) > AUTH_PASSWORD_MAX_BYTES:
        raise ValueError(
            f"Password is too long. bcrypt supports at most {AUTH_PASSWORD_MAX_BYTES} bytes."
        )


def hash_password(password: str) -> str:
    validate_new_password(password)

    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=AUTH_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not isinstance(password, str):
        return False

    stored_hash = str(password_hash or "").strip()
    if not password or not stored_hash:
        return False

    try:
        return bool(
            bcrypt.checkpw(
                password.encode("utf-8"),
                stored_hash.encode("utf-8"),
            )
        )
    except (TypeError, ValueError):
        return False