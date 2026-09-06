"""Regras determinísticas aplicadas antes de qualquer geração por LLM."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


PROHIBITED_REQUEST_PATTERNS = (
    re.compile(r"\b(prescrev|receit|recomend).{0,30}\b(medicamento|remedio|dose)"),
    re.compile(r"\b(aument|diminu|ajust|alter|troc|suspend).{0,25}\b(dose|medicamento|remedio)"),
    re.compile(r"\bqual (?:o )?(?:melhor )?(?:medicamento|remedio|dose)"),
    re.compile(r"\bdiagnostic"),
)

EMERGENCY_SYMPTOMS = {
    "dor toracica",
    "falta de ar",
    "confusao",
    "alteracao neurologica subita",
    "convulsao",
    "alteracao importante do nivel de consciencia",
}


def normalize_text(value: str) -> str:
    """Normaliza acentos, caixa e espaços para comparação de regras."""
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_accents.casefold().split())


def is_prohibited_request(question: str) -> bool:
    normalized = normalize_text(question)
    return any(pattern.search(normalized) for pattern in PROHIBITED_REQUEST_PATTERNS)


def find_emergency_symptoms(record: dict[str, Any]) -> list[str]:
    """Retorna apenas sintomas explicitamente registrados como alerta."""
    symptoms = record.get("reported_symptoms") or []
    return [item for item in symptoms if normalize_text(item) in EMERGENCY_SYMPTOMS]


def find_missing_fields(record: dict[str, Any]) -> list[str]:
    """Identifica campos mínimos ausentes sem inferir informações."""
    missing: list[str] = []
    if record.get("latest_vitals") is None:
        missing.append("latest_vitals")
    if record.get("last_follow_up") is None:
        missing.append("last_follow_up")
    if not record.get("medications"):
        missing.append("medications")
    if not record.get("exams"):
        missing.append("exams")
    return missing


def classify_priority(record: dict[str, Any]) -> str:
    """Classifica o cenário acadêmico usando apenas regras explícitas."""
    if find_emergency_symptoms(record):
        return "revisao_imediata"
    if find_missing_fields(record):
        return "dados_insuficientes"

    has_pending_exams = any(exam.get("status") == "pending" for exam in record.get("exams", []))
    notes_request_review = "requer revisao clinica" in normalize_text(record.get("notes", ""))
    needs_review = has_pending_exams or notes_request_review
    return "revisao_clinica" if needs_review else "rotina"
