from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from cryptography.fernet import Fernet

from qshield.config import settings


class HIPAASecurityEngine:
    """تشفير وحماية البيانات الطبية الحساسة وفق أنماط HIPAA."""

    def __init__(self) -> None:
        self._fernet = Fernet(self._load_or_create_key())

    def _load_or_create_key(self) -> bytes:
        if settings.encryption_key:
            key = settings.encryption_key.encode()
            settings.key_file.write_bytes(key)
            return key

        if settings.key_file.exists():
            return settings.key_file.read_bytes().strip()

        key = Fernet.generate_key()
        settings.key_file.write_bytes(key)
        return key

    def anonymize_patient_data(self, patient_id: str, national_id: str) -> str:
        """تعمية هوية المريض (De-identification) باستخدام HMAC-SHA256."""
        material = f"{patient_id}:{national_id}".encode("utf-8")
        digest = hmac.new(
            settings.identity_salt.encode("utf-8"),
            material,
            hashlib.sha256,
        )
        return digest.hexdigest()

    def encrypt_payload(self, data: dict[str, Any] | str) -> str:
        """تشفير البيانات الطبية أثناء النقل وفي حالة السكون (AES via Fernet)."""
        serialized = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
        return self._fernet.encrypt(serialized.encode("utf-8")).decode("utf-8")

    def decrypt_payload(self, token: str) -> dict[str, Any] | str:
        raw = self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
