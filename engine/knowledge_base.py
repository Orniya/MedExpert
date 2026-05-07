"""Load and validate symptom catalog and disease knowledge base."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


@dataclass(frozen=True)
class Symptom:
    id: str
    label: str
    category: str
    synonyms: tuple[str, ...]


@dataclass(frozen=True)
class Disease:
    id: str
    name: str
    required: frozenset[str]
    common: frozenset[str]
    rare: frozenset[str]
    severity: str
    risk_modifiers: dict[str, Any]
    treatment: tuple[str, ...]


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_symptoms(path: Path | None = None) -> list[Symptom]:
    p = path or (DATA_DIR / "symptoms.json")
    raw = _load_json(p)
    out: list[Symptom] = []
    seen: set[str] = set()
    for row in raw:
        sid = row["id"]
        if sid in seen:
            raise ValueError(f"Duplicate symptom id: {sid}")
        seen.add(sid)
        out.append(
            Symptom(
                id=sid,
                label=row["label"],
                category=row.get("category", "general"),
                synonyms=tuple(row.get("synonyms") or ()),
            )
        )
    return out


def load_diseases(
    symptom_ids: frozenset[str],
    path: Path | None = None,
) -> list[Disease]:
    p = path or (DATA_DIR / "diseases.json")
    raw = _load_json(p)
    diseases: list[Disease] = []
    seen_ids: set[str] = set()
    for row in raw:
        did = row["id"]
        if did in seen_ids:
            raise ValueError(f"Duplicate disease id: {did}")
        seen_ids.add(did)
        sym = row["symptoms"]
        req = frozenset(sym.get("required") or ())
        common = frozenset(sym.get("common") or ())
        rare = frozenset(sym.get("rare") or ())
        overlap = (req & common) | (req & rare) | (common & rare)
        if overlap:
            raise ValueError(f"Disease {did} has overlapping symptom tiers: {overlap}")
        all_s = req | common | rare
        unknown = all_s - symptom_ids
        if unknown:
            raise ValueError(f"Disease {did} references unknown symptoms: {sorted(unknown)}")
        diseases.append(
            Disease(
                id=did,
                name=row["name"],
                required=req,
                common=common,
                rare=rare,
                severity=row.get("severity", "Moderate"),
                risk_modifiers=row.get("risk_modifiers") or {"age": {}, "gender": {}},
                treatment=tuple(row.get("treatment") or ()),
            )
        )
    return diseases


def load_knowledge_base(
    symptoms_path: Path | None = None,
    diseases_path: Path | None = None,
) -> tuple[list[Symptom], list[Disease]]:
    symptoms = load_symptoms(symptoms_path)
    sids = frozenset(s.id for s in symptoms)
    diseases = load_diseases(sids, diseases_path)
    return symptoms, diseases


def symptoms_by_category(symptoms: list[Symptom]) -> dict[str, list[Symptom]]:
    buckets: dict[str, list[Symptom]] = {}
    for s in symptoms:
        buckets.setdefault(s.category, []).append(s)
    for k in buckets:
        buckets[k].sort(key=lambda x: x.label.lower())
    return dict(sorted(buckets.items(), key=lambda kv: kv[0].lower()))
