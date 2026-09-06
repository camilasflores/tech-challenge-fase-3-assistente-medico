from app.ui.presentation import build_result_view


def test_builds_view_for_model_fallback():
    view = build_result_view(
        {
            "final_answer": "Resumo seguro.",
            "priority": "revisao_clinica",
            "blocked": False,
            "human_validation_required": True,
            "model_name": "qwen+lora",
            "generation_fallback": True,
            "generation_fallback_reason": "missing_or_changed_exam_name",
            "sources": ["sqlite:records", "sqlite:records"],
            "executed_nodes": ["validate", "audit"],
            "run_id": "run-1",
        }
    )

    assert view["priority_label"] == "Revisão clínica"
    assert view["fallback_label"] == "Sim"
    assert view["fallback_reason"] == "missing_or_changed_exam_name"
    assert view["sources"] == ["sqlite:records"]


def test_marks_model_as_not_called_on_deterministic_route():
    view = build_result_view(
        {"priority": "bloqueado", "blocked": True, "final_answer": "Não posso."}
    )

    assert view["priority_label"] == "Pedido bloqueado"
    assert view["model_name"] == "Não acionado"
    assert view["fallback_label"] == "Não"
