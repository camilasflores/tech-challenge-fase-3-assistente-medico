"""Construção do contexto enviado ao modelo e validação de sua saída."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

from app.models.generator import ChatMessage
from app.safety.rules import normalize_text


SYSTEM_PROMPT = """Você é um assistente acadêmico de apoio à equipe médica.
Responda somente com base no prontuário sintético e nos protocolos fornecidos.
Não faça diagnóstico, prescrição, substituição, suspensão ou ajuste de dose.
Não invente dados ausentes. Seja objetivo, cite as fontes internas e declare que
a validação por profissional habilitado é obrigatória. Preserve exatamente os
nomes e identificadores recebidos e não crie números ou nomes de regras."""

UNSAFE_OUTPUT_PATTERNS = (
    re.compile(r"\b(tome|use|inicie|prescrevo)\b", re.IGNORECASE),
    re.compile(
        r"\b(aumente|diminua|ajuste|altere|suspenda)\b.{0,35}"
        r"\b(dose|medicamento|remedio)\b",
        re.IGNORECASE,
    ),
)


def build_generation_messages(state: Mapping[str, Any]) -> list[ChatMessage]:
    """Monta mensagens estruturadas sem pedir decisões clínicas ao modelo."""
    context = {
        "patient_id": state.get("patient_id"),
        "priority_already_defined_by_rules": state.get("priority"),
        "record": state.get("patient_record") or {},
        "protocol_excerpts": state.get("protocol_excerpts") or [],
        "sources": state.get("sources", []),
    }
    user_content = (
        f"Pergunta: {state.get('question', '')}\n\n"
        "Contexto autorizado (JSON):\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
        + "\n\nOrganize uma resposta. Não modifique a prioridade definida pelas regras."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def is_safe_generated_answer(answer: str) -> bool:
    """Rejeita saída vazia ou com comandos clínicos diretos."""
    normalized = answer.strip()
    if not normalized:
        return False
    return not any(pattern.search(normalized) for pattern in UNSAFE_OUTPUT_PATTERNS)


def validate_generated_answer(
    answer: str, state: Mapping[str, Any]
) -> tuple[bool, str | None]:
    """Valida segurança e fidelidade de fatos estruturados relevantes."""
    if not answer.strip():
        return False, "empty_answer"
    if not is_safe_generated_answer(answer):
        return False, "unsafe_clinical_command"

    normalized_answer = normalize_text(answer)
    normalized_question = normalize_text(state.get("question", ""))
    record = state.get("patient_record") or {}
    if "exame" in normalized_question or "pendente" in normalized_question:
        pending_exams = [
            exam["name"]
            for exam in record.get("exams", [])
            if exam.get("status") == "pending"
        ]
        missing = [
            name for name in pending_exams
            if normalize_text(name) not in normalized_answer
        ]
        if missing:
            return False, "missing_or_changed_exam_name"

    claimed_rules = set(re.findall(r"\bregra\s+\d+\b", normalized_answer))
    authorized_protocols = normalize_text(
        json.dumps(state.get("protocol_excerpts") or [], ensure_ascii=False)
    )
    if any(rule not in authorized_protocols for rule in claimed_rules):
        return False, "unsupported_rule_reference"
    return True, None
