from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Query

from .config import settings
from .models import Book, SearchResponse
from .scanner import LibraryIndex
from .search import match_score

app = FastAPI(title="E-Library", version="1.0.0")
index = LibraryIndex()


@app.on_event("startup")
def initial_scan() -> None:
    index.scan(settings.library_root)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/scan")
def rescan() -> dict:
    report = index.scan(settings.library_root)
    return report.model_dump()


@app.get("/books", response_model=SearchResponse)
def list_books(
    q: str | None = Query(default=None, description="Полнотекстовый запрос"),
    direction: str | None = None,
    program: str | None = None,
    fmt: str | None = Query(default=None, alias="format"),
    sort: str = Query(default="title", pattern="^(title|popular|rating|added)$"),
) -> SearchResponse:
    books = index.books

    if direction:
        books = [b for b in books if b.direction.lower() == direction.lower()]
    if program:
        books = [b for b in books if b.program.lower() == program.lower()]
    if fmt:
        books = [b for b in books if b.format.lower() == fmt.lower()]

    if q:
        scored: list[tuple[int, Book]] = []
        for book in books:
            score = match_score(q, book.title, book.author, " ".join(book.tags))
            if score:
                scored.append((score, book))
        scored.sort(key=lambda x: x[0], reverse=True)
        books = [item[1] for item in scored]

    if sort == "title":
        books.sort(key=lambda b: b.title.lower())
    elif sort == "popular":
        books.sort(key=lambda b: b.title.lower())
    elif sort == "rating":
        books.sort(key=lambda b: b.title.lower())
    elif sort == "added":
        books.sort(key=lambda b: b.indexed_at, reverse=True)
    else:
        books.sort(key=lambda b: b.title.lower())

    return SearchResponse(total=len(books), items=books)


def _sign(book_path: Path, expires_at: datetime) -> str:
    payload = f"{book_path}|{int(expires_at.timestamp())}"
    return hmac.new(settings.signing_key.encode(), payload.encode(), hashlib.sha256).hexdigest()


@app.get("/books/{book_id:path}/dynamic-link")
def dynamic_link(book_id: str) -> dict[str, str]:
    item = index.get(book_id)
    if not item:
        raise HTTPException(status_code=404, detail="Book not found")

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.dynamic_link_ttl_seconds)
    signature = _sign(Path(item.path), expires_at)
    query = urlencode({"book": item.path, "exp": int(expires_at.timestamp()), "sig": signature})
    return {"url": f"/download?{query}", "expires_at": expires_at.isoformat()}


@app.get("/download")
def validate_download(book: str, exp: int, sig: str) -> dict[str, str]:
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=403, detail="Link expired")

    expected = _sign(Path(book), expires_at)
    if not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=403, detail="Invalid signature")

    item = index.get(book)
    if not item:
        raise HTTPException(status_code=404, detail="Book not found")

    return {"status": "ok", "book": item.path}


@app.get("/books/{book_id:path}", response_model=Book)
def get_book(book_id: str) -> Book:
    item = index.get(book_id)
    if not item:
        raise HTTPException(status_code=404, detail="Book not found")
    return item
