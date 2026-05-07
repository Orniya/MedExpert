"""Confidence scoring, risk modifiers, severity classification, and top-N ranking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.backward_chaining import flatten_proof_trace, prove_disease
from engine.forward_chaining import infer_forward
from engine.knowledge_base import Disease, Symptom

W_REQ = 3.0
W_COMM = 1.5
W_RARE = 0.7


def _severity_rank(label: str) -> int:
    return {"Minor": 0, "Moderate": 1, "Urgent": 2}.get(label, 1)


def _rank_to_severity(r: int) -> str:
    for k, v in {"Minor": 0, "Moderate": 1, "Urgent": 2}.items():
        if v == r:
            return k
    return "Moderate"


def patient_has_red_flag(symptoms: set[str]) -> bool:
    """Clinical-style red flags for educational escalation only."""
    if {"chest_pain", "shortness_of_breath"} <= symptoms:
        return True
    if {"severe_headache", "stiff_neck"} <= symptoms:
        return True
    if "confusion" in symptoms and "fever" in symptoms:
        return True
    if {"blood_in_stool", "abdominal_pain"} <= symptoms:
        return True
    if "blood_in_urine" in symptoms and ("flank_pain" in symptoms or "fever" in symptoms):
        return True
    return False


def age_modifier(age: int | None, rules: dict[str, float] | None) -> float:
    if age is None or not rules:
        return 1.0
    m = 1.0
    for key, val in rules.items():
        if key.startswith("gte_"):
            n = int(key[4:])
            if age >= n:
                m *= float(val)
        elif key.startswith("lte_"):
            n = int(key[4:])
            if age <= n:
                m *= float(val)
    return min(m, 2.0)


def gender_modifier(gender: str | None, rules: dict[str, float] | None) -> float:
    if not gender or not rules:
        return 1.0
    g = gender.strip().lower()
    if g in ("m", "male"):
        return float(rules.get("male", 1.0))
    if g in ("f", "female"):
        return float(rules.get("female", 1.0))
    return 1.0


def _max_raw_score(d: Disease) -> float:
    return (
        W_REQ * len(d.required)
        + W_COMM * len(d.common)
        + W_RARE * len(d.rare)
    )


def _raw_match_score(d: Disease, matched_r: set[str], matched_c: set[str], matched_ra: set[str]) -> float:
    return (
        W_REQ * len(matched_r & d.required)
        + W_COMM * len(matched_c & d.common)
        + W_RARE * len(matched_ra & d.rare)
    )


@dataclass
class DiagnosisResult:
    disease_id: str
    disease_name: str
    confidence: float
    severity: str
    matched_required: list[str]
    matched_common: list[str]
    matched_rare: list[str]
    missing_required: list[str]
    unmatched_common: list[str]
    treatment: list[str]
    forward_iteration: int
    backward_proof_lines: list[str]
    age_modifier: float
    gender_modifier: float


def _disease_by_id(diseases: list[Disease]) -> dict[str, Disease]:
    return {d.id: d for d in diseases}


def diagnose(
    patient_symptoms: set[str],
    diseases: list[Disease],
    symptoms_catalog: list[Symptom],
    age: int | None = None,
    gender: str | None = None,
    top_n: int = 3,
) -> tuple[list[DiagnosisResult], dict[str, Any]]:
    """
    Run forward chaining, score fired rules, attach backward proof traces.
    Returns (ranked results, metadata dict).
    """
    by_id = _disease_by_id(diseases)
    label_by_id = {s.id: s.label for s in symptoms_catalog}
    forward_hits = infer_forward(patient_symptoms, diseases)
    red = patient_has_red_flag(patient_symptoms)

    scored: list[DiagnosisResult] = []
    for fc in forward_hits:
        if not fc.fired:
            continue
        d = by_id[fc.disease_id]
        rm = set(fc.matched_required)
        cm = set(fc.matched_common)
        ram = set(fc.matched_rare)
        raw = _raw_match_score(d, rm, cm, ram)
        denom = _max_raw_score(d) or 1.0
        rm_age = age_modifier(age, (d.risk_modifiers.get("age") or {}))
        rm_gen = gender_modifier(gender, (d.risk_modifiers.get("gender") or {}))
        conf = min(99.0, max(0.0, 100.0 * raw * rm_age * rm_gen / denom))

        base_sev = d.severity
        if red:
            base_sev = _rank_to_severity(max(_severity_rank(base_sev), _severity_rank("Urgent")))

        proved, proof = prove_disease(d, patient_symptoms)
        proof_lines = flatten_proof_trace(proof) if proved else [f"N goal: backward check failed for {d.id}"]

        missing_req = sorted(d.required - rm)
        unmatched_c = sorted(d.common - cm)

        scored.append(
            DiagnosisResult(
                disease_id=d.id,
                disease_name=d.name,
                confidence=round(conf, 1),
                severity=base_sev,
                matched_required=sorted(label_by_id.get(x, x) for x in rm),
                matched_common=sorted(label_by_id.get(x, x) for x in cm),
                matched_rare=sorted(label_by_id.get(x, x) for x in ram),
                missing_required=sorted(label_by_id.get(x, x) for x in missing_req),
                unmatched_common=sorted(label_by_id.get(x, x) for x in unmatched_c),
                treatment=list(d.treatment),
                forward_iteration=fc.iteration,
                backward_proof_lines=proof_lines,
                age_modifier=rm_age,
                gender_modifier=rm_gen,
            )
        )

    scored.sort(key=lambda r: (-r.confidence, r.disease_name))
    top = scored[:top_n]
    meta = {
        "red_flag_escalation": red,
        "forward_rules_fired": len(forward_hits),
        "symptom_count": len(patient_symptoms),
    }
    return top, meta


