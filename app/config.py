from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    library_root: Path
    dynamic_link_ttl_seconds: int
    signing_key: str

    @staticmethod
    def from_env() -> "Settings":
        root = os.getenv("ELIBRARY_ROOT", "./library")
        ttl = int(os.getenv("ELIBRARY_LINK_TTL", "300"))
        signing_key = os.getenv("ELIBRARY_SIGNING_KEY", "").strip()
        if not signing_key:
            # Эфемерный ключ безопаснее публичного дефолта; ссылки инвалидируются после рестарта.
            signing_key = secrets.token_urlsafe(32)
        return Settings(
            library_root=Path(root).resolve(),
            dynamic_link_ttl_seconds=ttl,
            signing_key=signing_key,
        )


settings = Settings.from_env()
