from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

from .metadata import infer_title_and_author
from .models import Book, MediaAsset, ScanReport

BOOK_FORMATS = {".pdf", ".epub", ".fb2", ".djvu", ".docx"}
IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_FORMATS = {".mp3", ".wav", ".ogg", ".m4a"}
VIDEO_FORMATS = {".mp4", ".webm", ".mov", ".mkv"}


class LibraryIndex:
    def __init__(self) -> None:
        self._books: dict[str, Book] = {}
        self._last_scan: ScanReport | None = None
        self._lock = RLock()

    @property
    def books(self) -> list[Book]:
        with self._lock:
            return list(self._books.values())

    @property
    def last_scan(self) -> ScanReport | None:
        with self._lock:
            return self._last_scan

    def get(self, book_id: str) -> Book | None:
        with self._lock:
            return self._books.get(book_id)

    def clear(self) -> None:
        with self._lock:
            self._books = {}
            self._last_scan = None

    def scan(self, root: Path) -> ScanReport:
        root = root.resolve()
        scanned = 0
        skipped = 0
        indexed: dict[str, Book] = {}
        now = datetime.now(timezone.utc)

        if not root.exists():
            root.mkdir(parents=True, exist_ok=True)

        all_files = [p for p in root.rglob("*") if p.is_file()]
        media_map: dict[str, list[MediaAsset]] = {}

        for file_path in all_files:
            scanned += 1
            suffix = file_path.suffix.lower()
            if suffix in IMAGE_FORMATS:
                media_type = "image"
            elif suffix in AUDIO_FORMATS:
                media_type = "audio"
            elif suffix in VIDEO_FORMATS:
                media_type = "video"
            else:
                continue

            key = str(file_path.with_suffix("").relative_to(root))
            media_map.setdefault(key, []).append(
                MediaAsset(type=media_type, path=str(file_path.relative_to(root)))
            )

        for file_path in all_files:
            suffix = file_path.suffix.lower()
            if suffix not in BOOK_FORMATS:
                skipped += 1
                continue

            rel = file_path.relative_to(root)
            parts = rel.parts
            direction = parts[0] if len(parts) > 1 else "Общее"
            program = parts[1] if len(parts) > 2 else "Базовая программа"

            title, author, language = infer_title_and_author(file_path)

            book_id = str(rel)
            key = str(file_path.with_suffix("").relative_to(root))
            indexed[book_id] = Book(
                id=book_id,
                title=title,
                author=author,
                language=language,
                format=suffix.lstrip("."),
                direction=direction,
                program=program,
                path=str(rel),
                media=media_map.get(key, []),
                indexed_at=now,
                tags=[direction, program, suffix.lstrip(".")],
            )

        report = ScanReport(
            root=root,
            scanned_files=scanned,
            indexed_books=len(indexed),
            skipped_files=skipped,
            timestamp=now,
        )
        with self._lock:
            self._books = indexed
            self._last_scan = report
            return report
