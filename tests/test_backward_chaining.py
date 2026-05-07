from engine.backward_chaining import infer_backward_all, prove_disease
from engine.knowledge_base import load_knowledge_base


def test_backward_proves_when_required_met():
    _, diseases = load_knowledge_base()
    d = next(x for x in diseases if x.id == "influenza")
    ok, proof = prove_disease(d, {"fever", "fatigue", "cough"})
    assert ok is True
    assert proof.satisfied is True


def test_backward_fails_when_required_missing():
    _, diseases = load_knowledge_base()
    d = next(x for x in diseases if x.id == "influenza")
    ok, proof = prove_disease(d, {"fatigue", "cough"})
    assert ok is False
    assert proof.satisfied is False


def test_backward_runs_all_goals():
    _, diseases = load_knowledge_base()
    out = infer_backward_all({"fever", "cough"}, diseases)
    assert len(out) == len(diseases)
    assert "influenza" in out
