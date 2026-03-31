from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

TITLE_SPLIT_RE = re.compile(r"[_\-.]+")
AUTHOR_TITLE_RE = re.compile(r"^(?P<author>[^-]+?)\s*-\s*(?P<title>.+)$")


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def title_from_filename(path: Path) -> tuple[str, str | None]:
    raw = path.stem
    raw = TITLE_SPLIT_RE.sub(" ", raw)
    raw = normalize_spaces(raw)

    m = AUTHOR_TITLE_RE.match(raw)
    if m:
        author = normalize_spaces(m.group("author"))
        title = normalize_spaces(m.group("title"))
        return title, author
    return raw, None


def parse_sidecar(path: Path) -> dict:
    sidecar = path.with_suffix(path.suffix + ".json")
    if sidecar.exists():
        try:
            return json.loads(sidecar.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def extract_pdf_title(path: Path) -> str | None:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        if reader.metadata and reader.metadata.title:
            return normalize_spaces(str(reader.metadata.title))
        if reader.pages:
            text = normalize_spaces((reader.pages[0].extract_text() or "")[:200])
            if text:
                return text.split(".")[0][:120]
    except Exception:
        return None
    return None


def extract_epub_title(path: Path) -> str | None:
    try:
        from ebooklib import epub  # type: ignore

        book = epub.read_epub(str(path))
        titles = book.get_metadata("DC", "title")
        if titles:
            return normalize_spaces(titles[0][0])
    except Exception:
        return None
    return None


def extract_fb2_title(path: Path) -> str | None:
    try:
        tree = ElementTree.parse(path)
        root = tree.getroot()
        ns = {"fb2": "http://www.gribuser.ru/xml/fictionbook/2.0"}
        title = root.find(".//fb2:book-title", ns)
        if title is not None and title.text:
            return normalize_spaces(title.text)
    except Exception:
        return None
    return None


def extract_docx_title(path: Path) -> str | None:
    try:
        with zipfile.ZipFile(path) as zf:
            with zf.open("docProps/core.xml") as core:
                xml = core.read()
                root = ElementTree.fromstring(xml)
                for element in root:
                    if element.tag.endswith("title") and element.text:
                        return normalize_spaces(element.text)
    except Exception:
        return None
    return None


def detect_language(text: str) -> str | None:
    if re.search(r"[А-Яа-яЁё]", text):
        return "ru"
    if re.search(r"[A-Za-z]", text):
        return "en"
    return None


def infer_title_and_author(path: Path) -> tuple[str, str | None, str | None]:
    sidecar = parse_sidecar(path)
    if sidecar.get("title"):
        title = normalize_spaces(str(sidecar["title"]))
        author = normalize_spaces(str(sidecar.get("author", ""))) or None
        language = sidecar.get("language")
        return title, author, language

    title, author = title_from_filename(path)

    deep_title = None
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        deep_title = extract_pdf_title(path)
    elif suffix == ".epub":
        deep_title = extract_epub_title(path)
    elif suffix == ".fb2":
        deep_title = extract_fb2_title(path)
    elif suffix == ".docx":
        deep_title = extract_docx_title(path)

    if deep_title:
        title = deep_title
    language = detect_language(title)
    return title, author, language
