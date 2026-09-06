from __future__ import annotations

import json

from app.observability.audit import AuditLogger


def test_audit_writes_minimal_jsonl_event(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    logger = AuditLogger(log_path)
    state = {
        "question": "Pergunta que não deve aparecer no log",
        "patient_id": "PAC-004",
        "patient_record": {"notes": "conteúdo clínico privado"},
        "final_answer": "Resposta que não deve aparecer no log",
        "request_status": "allowed",
        "priority": "revisao_imediata",
        "blocked": True,
        "human_validation_required": True,
        "model_name": "test_model",
        "generation_fallback": True,
        "generation_fallback_reason": "missing_or_changed_exam_name",
        "executed_nodes": ["validate_request", "emergency_response"],
        "sources": ["sqlite:medical_records", "sqlite:medical_records"],
    }

    event = logger.log(state)
    persisted = json.loads(log_path.read_text(encoding="utf-8"))

    assert persisted == event
    assert persisted["patient_id"] == "PAC-004"
    assert persisted["triggered_rules"] == ["emergency_symptoms"]
    assert persisted["sources"] == ["sqlite:medical_records"]
    assert persisted["generation_fallback_reason"] == "missing_or_changed_exam_name"
    assert "question" not in persisted
    assert "patient_record" not in persisted
    assert "final_answer" not in persisted


def test_audit_does_not_persist_malformed_patient_identifier(tmp_path):
    logger = AuditLogger(tmp_path / "audit.jsonl")

    event = logger.log(
        {
            "patient_id": "PAC-001' OR 1=1",
            "request_status": "invalid",
            "executed_nodes": ["validate_request", "invalid_response"],
        }
    )

    assert event["patient_id"] is None
    assert event["triggered_rules"] == ["invalid_input"]
