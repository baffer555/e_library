from pathlib import Path

from fastapi.testclient import TestClient


def test_scan_and_search(monkeypatch, tmp_path: Path):
    root = tmp_path / "library"
    book_path = root / "Информатика" / "Python" / "Гвидо ван Россум - Введение в Python.pdf"
    media_path = root / "Информатика" / "Python" / "Гвидо ван Россум - Введение в Python.mp4"
    book_path.parent.mkdir(parents=True, exist_ok=True)
    book_path.write_bytes(b"%PDF-1.4 test")
    media_path.write_bytes(b"video")

    monkeypatch.setenv("ELIBRARY_ROOT", str(root))

    from app.main import app, index, settings

    settings.library_root = root
    index.scan(root)

    client = TestClient(app)
    scan_resp = client.post("/scan")
    assert scan_resp.status_code == 200
    assert scan_resp.json()["indexed_books"] == 1

    resp = client.get("/books", params={"q": "python"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["direction"] == "Информатика"
    assert data["items"][0]["program"] == "Python"
    assert data["items"][0]["media"][0]["type"] == "video"


def test_dynamic_link(monkeypatch, tmp_path: Path):
    root = tmp_path / "library"
    book_path = root / "Math" / "Algebra" / "Linear Algebra.pdf"
    book_path.parent.mkdir(parents=True, exist_ok=True)
    book_path.write_bytes(b"%PDF-1.4 test")

    monkeypatch.setenv("ELIBRARY_ROOT", str(root))

    from app.main import app, index, settings

    settings.library_root = root
    index.scan(root)
    client = TestClient(app)
    item_id = "Math/Algebra/Linear Algebra.pdf"

    link_resp = client.get(f"/books/{item_id}/dynamic-link")
    assert link_resp.status_code == 200

    url = link_resp.json()["url"]
    download = client.get(url)
    assert download.status_code == 200
