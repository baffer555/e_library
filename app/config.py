from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    library_root: Path
    dynamic_link_ttl_seconds: int = 300

    @staticmethod
    def from_env() -> "Settings":
        root = os.getenv("ELIBRARY_ROOT", "./library")
        ttl = int(os.getenv("ELIBRARY_LINK_TTL", "300"))
        return Settings(library_root=Path(root).resolve(), dynamic_link_ttl_seconds=ttl)


settings = Settings.from_env()
