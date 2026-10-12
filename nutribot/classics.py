"""Load and search a small curated selection from Waijing Weiyan."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path


_WAIJING_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "classics"
    / "waijing.json"
)

_STOP_WORDS = {
    "the", "and", "for", "with", "how", "what", "why", "when", "where",
    "who", "are", "was", "were", "have", "has", "had", "this", "that",
    "these", "those", "from", "into", "not", "but", "you", "your", "our",
    "their",
}


def _search_words(text: str) -> set[str]:
    """Tokenize English words and individual Han characters for matching."""
    tokens = re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]|[a-z0-9]+", text.casefold())
    return {
        token
        for token in tokens
        if (
            "\u3400" <= token <= "\u9fff"
            or (len(token) >= 3 and token not in _STOP_WORDS)
        )
    }


@lru_cache(maxsize=1)
def load_waijing() -> dict:
    """Load and cache the curated Waijing reference document."""
    with _WAIJING_PATH.open("r", encoding="utf-8") as source_file:
        return json.load(source_file)


def find_passages(query: str, max_matches: int = 3) -> list[dict]:
    """Return passages ranked by the number of query words in their text."""
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    if isinstance(max_matches, bool) or not isinstance(max_matches, int):
        raise TypeError("max_matches must be an integer")
    if max_matches <= 0:
        return []

    query_words = _search_words(query)
    if not query_words:
        return []

    scored = []
    for order, passage in enumerate(load_waijing()["passages"]):
        passage_words = _search_words(passage["text"])
        score = len(query_words & passage_words)
        if score:
            scored.append((score, order, passage))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [
        {key: passage[key] for key in ("id", "theme", "text")}
        for _score, _order, passage in scored[:max_matches]
    ]


def get_disclaimer() -> str:
    """Return the source's authenticity and educational-use note."""
    return load_waijing()["authenticity_note"]
