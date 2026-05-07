from engine.forward_chaining import infer_forward
from engine.knowledge_base import load_knowledge_base


def test_forward_chaining_fires_when_required_present():
    symptoms, diseases = load_knowledge_base()
    facts = {"fever", "fatigue", "cough", "sore_throat", "muscle_aches"}
    out = infer_forward(facts, diseases)
    ids = {x.disease_id for x in out}
    assert "influenza" in ids


def test_forward_chaining_does_not_fire_missing_required():
    symptoms, diseases = load_knowledge_base()
    facts = {"fatigue", "cough"}
    out = infer_forward(facts, diseases)
    ids = {x.disease_id for x in out}
    assert "influenza" not in ids
