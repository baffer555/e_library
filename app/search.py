from __future__ import annotations

import re

RUS_STOPWORDS = {
    "и",
    "в",
    "на",
    "по",
    "для",
    "о",
    "об",
    "а",
    "но",
    "или",
}

SUFFIXES = (
    "ами",
    "ями",
    "ого",
    "его",
    "ому",
    "ему",
    "иях",
    "ах",
    "ях",
    "ов",
    "ев",
    "ий",
    "ый",
    "ая",
    "ое",
    "ые",
    "ой",
    "ых",
    "ам",
    "ям",
    "ом",
    "ем",
    "ую",
    "юю",
    "а",
    "я",
    "ы",
    "и",
    "у",
    "ю",
    "е",
    "о",
)


def normalize_token(token: str) -> str:
    token = token.lower().strip()
    token = re.sub(r"[^\wа-яё]", "", token)
    for suffix in SUFFIXES:
        stem_length = len(token) - len(suffix)
        min_stem_length = 4 if len(suffix) == 1 else 3
        if token.endswith(suffix) and stem_length >= min_stem_length:
            token = token[: -len(suffix)]
            break
    return token


def tokenize(text: str) -> set[str]:
    parts = re.split(r"\s+", text.lower())
    tokens = {normalize_token(part) for part in parts if part}
    return {t for t in tokens if t and t not in RUS_STOPWORDS}


def match_score(query: str, *fields: str | None) -> int:
    q_tokens = tokenize(query)
    if not q_tokens:
        return 0

    corpus = " ".join(f for f in fields if f)
    c_tokens = tokenize(corpus)
    return len(q_tokens.intersection(c_tokens))
