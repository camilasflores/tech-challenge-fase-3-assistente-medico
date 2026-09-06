from app.safety.rules import (
    classify_priority,
    find_emergency_symptoms,
    is_prohibited_request,
)


def test_detects_prohibited_medication_and_diagnosis_requests():
    assert is_prohibited_request("Pode aumentar a dose do remédio?")
    assert is_prohibited_request("Você pode diagnosticar hipertensão?")
    assert not is_prohibited_request("Quais exames estão pendentes?")


def test_emergency_requires_explicit_recorded_symptom():
    assert find_emergency_symptoms({"reported_symptoms": ["dor torácica"]}) == ["dor torácica"]
    assert find_emergency_symptoms({"reported_symptoms": []}) == []


def test_missing_data_has_priority_before_common_flow():
    record = {"latest_vitals": None, "last_follow_up": None, "medications": [], "exams": []}
    assert classify_priority(record) == "dados_insuficientes"

