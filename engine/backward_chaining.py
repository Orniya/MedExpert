"""Backward chaining: goal-driven proof of disease hypotheses against patient facts."""

from __future__ import annotations

from dataclasses import dataclass

from engine.knowledge_base import Disease


@dataclass(frozen=True)
class ProofNode:
    kind: str  # "AND" | "SYMPTOM" | "OR_GROUP"
    label: str
    satisfied: bool
    children: tuple["ProofNode", ...] = ()


def _prove_required(
    disease: Disease,
    facts: set[str],
) -> tuple[bool, ProofNode]:
    """AND over all required symptoms."""
    children: list[ProofNode] = []
    all_ok = True
    for sid in sorted(disease.required):
        ok = sid in facts
        all_ok = all_ok and ok
        children.append(ProofNode(kind="SYMPTOM", label=sid, satisfied=ok))
    return all_ok, ProofNode(
        kind="AND",
        label=f"required({disease.id})",
        satisfied=all_ok,
        children=tuple(children),
    )


def _prove_common_boost(
    disease: Disease,
    facts: set[str],
) -> ProofNode:
    """
    OR-group: at least one common symptom present counts as optional 'boost' branch.
    Represent as OR over each common symptom being true in facts.
    """
    children: list[ProofNode] = []
    any_ok = False
    for sid in sorted(disease.common):
        ok = sid in facts
        any_ok = any_ok or ok
        children.append(ProofNode(kind="SYMPTOM", label=f"common:{sid}", satisfied=ok))
    return ProofNode(
        kind="OR_GROUP",
        label=f"any_common({disease.id})",
        satisfied=any_ok,
        children=tuple(children),
    )


def prove_disease(disease: Disease, facts: set[str]) -> tuple[bool, ProofNode]:
    """
    Disease goal is proved iff all required symptoms are in facts.
    Returns proof tree for reporting.
    """
    req_ok, req_node = _prove_required(disease, facts)
    common_node = _prove_common_boost(disease, facts)
    root = ProofNode(
        kind="AND",
        label=f"goal({disease.id})",
        satisfied=req_ok,
        children=(req_node, common_node),
    )
    return req_ok, root


def infer_backward_all(
    patient_symptoms: set[str],
    diseases: list[Disease],
) -> dict[str, tuple[bool, ProofNode]]:
    """Run backward proof for every disease; used for report traces."""
    out: dict[str, tuple[bool, ProofNode]] = {}
    facts = set(patient_symptoms)
    for d in diseases:
        out[d.id] = prove_disease(d, facts)
    return out


def flatten_proof_trace(node: ProofNode, indent: int = 0) -> list[str]:
    pad = "  " * indent
    mark = "Y" if node.satisfied else "N"
    lines = [f"{pad}[{mark}] {node.kind}: {node.label}"]
    for ch in node.children:
        lines.extend(flatten_proof_trace(ch, indent + 1))
    return lines
