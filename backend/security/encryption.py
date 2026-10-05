"""Authenticated encryption for stored search text using a persistent local key."""
import os
from pathlib import Path
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

PREFIX = "fernet:v1:"


def _cipher():
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    key = os.getenv("DATA_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("DATA_ENCRYPTION_KEY is required for stored history encryption")
    return Fernet(key.encode())


def encrypt_data(data: str) -> bytes:
    return _cipher().encrypt(data.encode())


def decrypt_data(token: bytes) -> str:
    return _cipher().decrypt(token).decode()


def encrypt_stored_text(value: str) -> str:
    return PREFIX + encrypt_data(value).decode()


def decrypt_stored_text(value: str) -> str:
    # Legacy plaintext is supported only for the startup migration.
    return decrypt_data(value[len(PREFIX):].encode()) if value.startswith(PREFIX) else value


class EncryptedText(TypeDecorator):
    """ORM reads authorized plaintext, while database writes are ciphertext."""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return encrypt_stored_text(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return decrypt_stored_text(value) if value is not None else None
