"""Transforma o estado técnico do grafo em dados simples para a interface."""

from __future__ import annotations

from typing import Any, Mapping


PRIORITY_LABELS = {
    "rotina": "Rotina",
    "revisao_clinica": "Revisão clínica",
    "revisao_imediata": "Revisão imediata",
    "dados_insuficientes": "Dados insuficientes",
    "bloqueado": "Pedido bloqueado",
}


def build_result_view(result: Mapping[str, Any]) -> dict[str, Any]:
    """Seleciona apenas os campos necessários à tela de demonstração."""
    priority = result.get("priority") or "não classificada"
    model_name = result.get("model_name") or "Não acionado"
    fallback = bool(result.get("generation_fallback"))
    return {
        "answer": result.get("final_answer", "Resposta indisponível."),
        "priority": priority,
        "priority_label": PRIORITY_LABELS.get(priority, priority.replace("_", " ").title()),
        "blocked": bool(result.get("blocked")),
        "human_validation_required": bool(
            result.get("human_validation_required")
        ),
        "model_name": model_name,
        "fallback": fallback,
        "fallback_label": "Sim" if fallback else "Não",
        "fallback_reason": result.get("generation_fallback_reason"),
        "sources": list(dict.fromkeys(result.get("sources", []))),
        "executed_nodes": result.get("executed_nodes", []),
        "run_id": result.get("run_id"),
        "audited_at": result.get("audited_at"),
    }

