"""Authenticated encryption for stored user provider credentials."""

from __future__ import annotations

import os
from typing import List

from cryptography.fernet import Fernet, InvalidToken, MultiFernet


AI_CREDENTIAL_FERNET_KEYS_ENV = "APPLYLENS_AI_CREDENTIAL_FERNET_KEYS"
AI_CREDENTIAL_ENCRYPTION_SCHEME = "fernet-v1"
_CREDENTIAL_MASK_PREFIX = "••••••••"


class ProviderCredentialCryptoError(ValueError):
    """Bounded credential-crypto failure that never includes secret material."""


def _load_fernet_keyring() -> MultiFernet:
    raw_keyring = str(os.environ.get(AI_CREDENTIAL_FERNET_KEYS_ENV, "") or "")
    key_values = [
        item.strip()
        for item in raw_keyring.split(",")
        if item.strip()
    ]
    if not key_values:
        raise ProviderCredentialCryptoError(
            "AI provider credential encryption keyring is not configured."
        )

    fernets: List[Fernet] = []
    try:
        for key_value in key_values:
            fernets.append(Fernet(key_value.encode("ascii")))
    except Exception:
        raise ProviderCredentialCryptoError(
            "AI provider credential encryption keyring is invalid."
        ) from None
    return MultiFernet(fernets)


def _credential_text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProviderCredentialCryptoError("Provider credential is required.")
    return value.strip()


def encrypt_provider_credential(credential: object) -> str:
    """Encrypt one plaintext provider credential with the active Fernet key."""

    plaintext = _credential_text(credential)
    try:
        return _load_fernet_keyring().encrypt(plaintext.encode("utf-8")).decode(
            "ascii"
        )
    except ProviderCredentialCryptoError:
        raise
    except Exception:
        raise ProviderCredentialCryptoError(
            "AI provider credential encryption failed."
        ) from None


def decrypt_provider_credential(ciphertext: object) -> str:
    """Decrypt one stored Fernet token using the configured rotation keyring."""

    if not isinstance(ciphertext, str) or not ciphertext.strip():
        raise ProviderCredentialCryptoError(
            "Stored AI provider credential is invalid."
        )
    try:
        plaintext = _load_fernet_keyring().decrypt(
            ciphertext.strip().encode("ascii")
        )
        return plaintext.decode("utf-8")
    except ProviderCredentialCryptoError:
        raise
    except (InvalidToken, UnicodeError, ValueError):
        raise ProviderCredentialCryptoError(
            "Stored AI provider credential could not be decrypted."
        ) from None
    except Exception:
        raise ProviderCredentialCryptoError(
            "Stored AI provider credential could not be decrypted."
        ) from None


def mask_provider_credential(credential: object) -> str:
    """Return a bounded hint that reveals no more than the last four characters."""

    plaintext = _credential_text(credential)
    if len(plaintext) <= 4:
        return _CREDENTIAL_MASK_PREFIX
    return f"{_CREDENTIAL_MASK_PREFIX}{plaintext[-4:]}"
