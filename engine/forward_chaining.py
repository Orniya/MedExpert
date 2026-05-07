"""Forward chaining: data-driven rule firing from patient facts (symptoms)."""

from __future__ import annotations

from dataclasses import dataclass

from engine.knowledge_base import Disease


@dataclass(frozen=True)
class ForwardCandidate:
    disease_id: str
    matched_required: frozenset[str]
    missing_required: frozenset[str]
    matched_common: frozenset[str]
    matched_rare: frozenset[str]
    fired: bool
    """True if all required symptoms were present when the rule fired."""
    iteration: int
    """Iteration index (0-based) when this candidate was first added to working memory."""


def infer_forward(
    patient_symptoms: set[str],
    diseases: list[Disease],
    max_iterations: int = 8,
) -> list[ForwardCandidate]:
    """
    Working memory starts as patient_symptoms.
    Each iteration, for every disease rule, if required ⊆ working_memory, add
    disease_id to fired set and record match details. Stops when no new diseases fire.
    """
    working: set[str] = set(patient_symptoms)
    fired_ids: set[str] = set()
    candidates: list[ForwardCandidate] = []
    iteration = 0
    changed = True
    while changed and iteration < max_iterations:
        changed = False
        for d in diseases:
            if d.id in fired_ids:
                continue
            req = d.required
            missing = req - working
            if missing:
                continue
            matched_r = req & working
            matched_c = d.common & working
            matched_ra = d.rare & working
            fired_ids.add(d.id)
            candidates.append(
                ForwardCandidate(
                    disease_id=d.id,
                    matched_required=frozenset(matched_r),
                    missing_required=frozenset(missing),
                    matched_common=frozenset(matched_c),
                    matched_rare=frozenset(matched_ra),
                    fired=True,
                    iteration=iteration,
                )
            )
            # Add abstract fact so chaining can represent derived conclusions
            working.add(f"possible_disease:{d.id}")
            changed = True
        iteration += 1
    return candidates
