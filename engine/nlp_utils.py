"""Map free-text patient descriptions to symptom IDs using synonym / substring heuristics."""

from __future__ import annotations

import re
from typing import Iterable

from engine.knowledge_base import Symptom


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def extract_symptoms_from_text(text: str, symptoms: Iterable[Symptom]) -> set[str]:
    """
    Return symptom IDs whose labels or synonyms appear as substrings in the text.
    Longer phrases are checked first to reduce false positives.
    """
    if not text or not text.strip():
        return set()
    norm = _normalize(text)
    if not norm:
        return set()
    found: set[str] = set()
    phrases: list[tuple[str, str]] = []
    for s in symptoms:
        phrases.append((s.id, s.label.lower()))
        for syn in s.synonyms:
            phrases.append((s.id, syn.lower()))
    # Longer phrases first
    phrases.sort(key=lambda x: len(x[1]), reverse=True)
    covered_spans: list[tuple[int, int]] = []

    def overlaps(start: int, end: int) -> bool:
        for a, b in covered_spans:
            if start < b and end > a:
                return True
        return False

    for sid, phrase in phrases:
        if len(phrase) < 2:
            continue
        start = 0
        while True:
            idx = norm.find(phrase, start)
            if idx == -1:
                break
            end = idx + len(phrase)
            if not overlaps(idx, end):
                found.add(sid)
                covered_spans.append((idx, end))
            start = idx + 1
    return found
