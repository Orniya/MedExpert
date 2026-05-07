from engine.diagnosis import age_modifier, diagnose, patient_has_red_flag
from engine.knowledge_base import load_knowledge_base


def test_age_modifier_applies_thresholds():
    rules = {"gte_65": 1.2, "lte_5": 1.3}
    assert age_modifier(70, rules) == 1.2
    assert age_modifier(3, rules) == 1.3
    assert age_modifier(30, rules) == 1.0


def test_red_flag_detection_true_for_chestpain_sob():
    assert patient_has_red_flag({"chest_pain", "shortness_of_breath"}) is True


def test_diagnose_returns_top_three_sorted():
    symptoms, diseases = load_knowledge_base()
    selected = {"fever", "fatigue", "cough", "sore_throat", "muscle_aches", "headache"}
    results, meta = diagnose(selected, diseases, symptoms, age=30, gender="female", top_n=3)
    assert len(results) <= 3
    if len(results) >= 2:
        assert results[0].confidence >= results[1].confidence
    assert meta["forward_rules_fired"] >= len(results)
