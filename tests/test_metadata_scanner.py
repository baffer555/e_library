import json
from pathlib import Path

from app.metadata import infer_title_and_author
from app.scanner import LibraryIndex


def test_infer_title_prefers_sidecar_and_detects_language(tmp_path: Path):
    book = tmp_path / "Author - Ignored Title.pdf"
    book.write_bytes(b"%PDF-1.4")
    sidecar = tmp_path / "Author - Ignored Title.pdf.json"
    sidecar.write_text(
        json.dumps({"title": "Алгоритмы и структуры данных", "author": "Иванов"}),
        encoding="utf-8",
    )

    title, author, language = infer_title_and_author(book)
    assert title == "Алгоритмы и структуры данных"
    assert author == "Иванов"
    assert language is None


def test_infer_title_fallback_filename_and_language(tmp_path: Path):
    book = tmp_path / "Robert Martin - Clean Code.docx"
    book.write_bytes(b"PK")

    title, author, language = infer_title_and_author(book)
    assert title == "Clean Code"
    assert author == "Robert Martin"
    assert language == "en"


def test_scanner_direction_program_defaults_and_media(tmp_path: Path):
    root = tmp_path / "library"
    root.mkdir()

    nested = root / "Data Science" / "ML" / "Intro to ML.pdf"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_bytes(b"%PDF-1.4")
    (nested.parent / "Intro to ML.mp3").write_bytes(b"audio")
    (nested.parent / "Intro to ML.jpg").write_bytes(b"image")

    flat = root / "SingleBook.pdf"
    flat.write_bytes(b"%PDF-1.4")

    index = LibraryIndex()
    report = index.scan(root)

    assert report.indexed_books == 2
    books = {b.id: b for b in index.books}

    assert books["Data Science/ML/Intro to ML.pdf"].direction == "Data Science"
    assert books["Data Science/ML/Intro to ML.pdf"].program == "ML"
    media_types = sorted([m.type for m in books["Data Science/ML/Intro to ML.pdf"].media])
    assert media_types == ["audio", "image"]

    assert books["SingleBook.pdf"].direction == "Общее"
    assert books["SingleBook.pdf"].program == "Базовая программа"
