from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class MediaAsset(BaseModel):
    type: str
    path: str


class Book(BaseModel):
    id: str
    title: str
    author: str | None = None
    year: int | None = None
    language: str | None = None
    format: str
    direction: str
    program: str
    path: str
    media: list[MediaAsset] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    indexed_at: datetime


class ScanReport(BaseModel):
    root: Path
    scanned_files: int
    indexed_books: int
    skipped_files: int
    timestamp: datetime


class SearchResponse(BaseModel):
    total: int
    items: list[Book]
