"""Contrato do estado compartilhado entre os nós do LangGraph."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class AssistantState(TypedDict, total=False):
    question: str
    patient_id: str
    request_status: str
    patient_record: dict[str, Any] | None
    priority: str
    missing_fields: list[str]
    alert_symptoms: list[str]
    protocol_excerpts: list[dict[str, Any]]
    final_answer: str
    blocked: bool
    human_validation_required: bool
    errors: list[str]
    executed_nodes: Annotated[list[str], operator.add]
    sources: Annotated[list[str], operator.add]

