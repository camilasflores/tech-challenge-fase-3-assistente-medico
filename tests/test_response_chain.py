from app.chains.response_chain import (
    SYSTEM_PROMPT,
    build_generation_messages,
    is_safe_generated_answer,
    validate_generated_answer,
)


def test_prompt_contains_context_sources_and_safety_limits():
    messages = build_generation_messages(
        {
            "question": "Quais exames estão pendentes?",
            "patient_id": "PAC-003",
            "priority": "revisao_clinica",
            "patient_record": {
                "exams": [{"name": "creatinina", "status": "pending"}]
            },
            "protocol_excerpts": [{"content": "Listar exames pendentes."}],
            "sources": ["data/protocols/PROTOCOLO_HAS_001.md"],
        }
    )

    assert messages[0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert "PAC-003" in messages[1]["content"]
    assert "creatinina" in messages[1]["content"]
    assert "PROTOCOLO_HAS_001.md" in messages[1]["content"]
    assert "Não faça diagnóstico" in SYSTEM_PROMPT


def test_output_validator_rejects_direct_clinical_commands():
    assert is_safe_generated_answer("Os dados exigem validação profissional.")
    assert not is_safe_generated_answer("")
    assert not is_safe_generated_answer("Tome losartana todos os dias.")
    assert not is_safe_generated_answer("Aumente a dose do medicamento.")


def test_grounding_validator_requires_exact_pending_exam_names():
    state = {
        "question": "Quais exames estão pendentes?",
        "patient_record": {
            "exams": [
                {"name": "creatinina", "status": "pending"},
                {"name": "perfil lipidico", "status": "pending"},
            ]
        },
        "protocol_excerpts": [],
    }

    valid, reason = validate_generated_answer(
        "Exames: Crânína e perfil lipídico.", state
    )

    assert valid is False
    assert reason == "missing_or_changed_exam_name"


def test_grounding_validator_rejects_invented_rule_number():
    valid, reason = validate_generated_answer(
        "Encaminhar para revisão clínica conforme Regra 2.",
        {
            "question": "Qual a prioridade?",
            "patient_record": {},
            "protocol_excerpts": [{"content": "Solicitar revisão clínica."}],
        },
    )

    assert valid is False
    assert reason == "unsupported_rule_reference"
