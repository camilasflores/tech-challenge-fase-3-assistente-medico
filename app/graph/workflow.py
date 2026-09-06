"""Fluxo seguro e auditável do assistente médico acadêmico."""

from __future__ import annotations

import re
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from app.chains.protocol_retriever import build_protocol_retriever
from app.chains.response_chain import (
    build_generation_messages,
    validate_generated_answer,
)
from app.database.repository import PatientRepository
from app.graph.state import AssistantState
from app.models.factory import create_generator_from_environment
from app.models.generator import TextGenerator
from app.observability.audit import AuditLogger
from app.safety.rules import (
    classify_priority,
    find_emergency_symptoms,
    find_missing_fields,
    is_prohibited_request,
)


PATIENT_ID_PATTERN = re.compile(r"PAC-\d{3}")
SECURITY_POLICY_SOURCE = "data/protocols/POLITICA_SEGURANCA_001.md"


def _format_pending_exams(record: dict[str, Any]) -> str:
    exams = [exam["name"] for exam in record.get("exams", []) if exam.get("status") == "pending"]
    return ", ".join(exams) if exams else "nenhum exame pendente registrado"


def build_assistant_graph(
    repository: PatientRepository | None = None,
    protocol_retriever: Any | None = None,
    audit_logger: AuditLogger | None = None,
    text_generator: TextGenerator | None = None,
):
    """Monta o grafo com dependências injetáveis para execução e testes."""
    patient_repository = repository or PatientRepository()
    retriever = protocol_retriever or build_protocol_retriever()
    auditor = audit_logger or AuditLogger()
    generator = text_generator or create_generator_from_environment()

    def validate_request(state: AssistantState) -> dict[str, Any]:
        question = state.get("question", "").strip()
        patient_id = state.get("patient_id", "").strip().upper()
        errors: list[str] = []
        if not question:
            errors.append("A pergunta é obrigatória.")
        if not PATIENT_ID_PATTERN.fullmatch(patient_id):
            errors.append("patient_id deve seguir o formato sintético PAC-000.")

        if errors:
            status = "invalid"
        elif is_prohibited_request(question):
            status = "prohibited"
        else:
            status = "allowed"
        return {
            "question": question,
            "patient_id": patient_id,
            "request_status": status,
            "errors": errors,
            "executed_nodes": ["validate_request"],
        }

    def route_request(state: AssistantState) -> Literal["invalid_response", "blocked_response", "load_patient"]:
        return {
            "invalid": "invalid_response",
            "prohibited": "blocked_response",
            "allowed": "load_patient",
        }[state["request_status"]]

    def invalid_response(state: AssistantState) -> dict[str, Any]:
        return {
            "final_answer": "Não foi possível processar a solicitação: " + " ".join(state["errors"]),
            "blocked": True,
            "human_validation_required": False,
            "executed_nodes": ["invalid_response"],
        }

    def blocked_response(_: AssistantState) -> dict[str, Any]:
        return {
            "priority": "bloqueado",
            "final_answer": (
                "Não posso diagnosticar, prescrever ou alterar medicamentos e doses. "
                "Essa decisão exige avaliação de um profissional habilitado."
            ),
            "blocked": True,
            "human_validation_required": True,
            "sources": [SECURITY_POLICY_SOURCE],
            "executed_nodes": ["blocked_response"],
        }

    def load_patient(state: AssistantState) -> dict[str, Any]:
        record = patient_repository.get_patient(state["patient_id"])
        return {
            "patient_record": record,
            "sources": ["sqlite:medical_records"],
            "executed_nodes": ["load_patient"],
        }

    def route_patient(state: AssistantState) -> Literal["not_found_response", "assess_patient"]:
        return "assess_patient" if state.get("patient_record") else "not_found_response"

    def not_found_response(state: AssistantState) -> dict[str, Any]:
        return {
            "final_answer": f"Paciente sintético não encontrado: {state['patient_id']}.",
            "blocked": True,
            "human_validation_required": False,
            "executed_nodes": ["not_found_response"],
        }

    def assess_patient(state: AssistantState) -> dict[str, Any]:
        record = state["patient_record"] or {}
        return {
            "priority": classify_priority(record),
            "missing_fields": find_missing_fields(record),
            "alert_symptoms": find_emergency_symptoms(record),
            "executed_nodes": ["assess_patient"],
        }

    def route_priority(state: AssistantState) -> Literal["emergency_response", "missing_data_response", "retrieve_protocols"]:
        if state["priority"] == "revisao_imediata":
            return "emergency_response"
        if state["priority"] == "dados_insuficientes":
            return "missing_data_response"
        return "retrieve_protocols"

    def emergency_response(state: AssistantState) -> dict[str, Any]:
        symptoms = ", ".join(state["alert_symptoms"])
        return {
            "final_answer": (
                f"REVISÃO IMEDIATA. Foram registrados sintomas de alerta: {symptoms}. "
                "Recomenda-se avaliação presencial imediata conforme o serviço de emergência local."
            ),
            "blocked": True,
            "human_validation_required": True,
            "sources": ["data/protocols/PROTOCOLO_HAS_001.md"],
            "executed_nodes": ["emergency_response"],
        }

    def missing_data_response(state: AssistantState) -> dict[str, Any]:
        fields = ", ".join(state["missing_fields"])
        return {
            "final_answer": (
                f"Dados insuficientes para organizar a análise. Campos ausentes: {fields}. "
                "A equipe deve completar e validar o prontuário."
            ),
            "blocked": False,
            "human_validation_required": True,
            "sources": ["data/protocols/PROTOCOLO_HAS_001.md"],
            "executed_nodes": ["missing_data_response"],
        }

    def retrieve_protocols(state: AssistantState) -> dict[str, Any]:
        documents = retriever.invoke(state["question"])
        excerpts = [
            {"content": document.page_content, **document.metadata}
            for document in documents
        ]
        sources = list(dict.fromkeys(item["source"] for item in excerpts))
        return {
            "protocol_excerpts": excerpts,
            "sources": sources,
            "executed_nodes": ["retrieve_protocols"],
        }

    def compose_response(state: AssistantState) -> dict[str, Any]:
        record = state["patient_record"] or {}
        vitals = record.get("latest_vitals") or {}
        pressure = (
            f"{vitals.get('systolic_bp')}/{vitals.get('diastolic_bp')} mmHg"
            if vitals
            else "não registrada"
        )
        safe_fallback = (
            f"Resumo do {state['patient_id']}: pressão mais recente {pressure}; "
            f"{_format_pending_exams(record)}. Prioridade: {state['priority']}. "
            "A interpretação e qualquer conduta exigem validação por profissional habilitado."
        )
        try:
            generated_answer = generator.generate(build_generation_messages(state))
            answer_is_safe, fallback_reason = validate_generated_answer(
                generated_answer, state
            )
        except Exception as error:
            generated_answer = ""
            answer_is_safe = False
            fallback_reason = f"generation_error:{type(error).__name__}"
        return {
            "final_answer": generated_answer if answer_is_safe else safe_fallback,
            "model_name": generator.model_name,
            "generation_fallback": not answer_is_safe,
            "generation_fallback_reason": fallback_reason,
            "blocked": False,
            "human_validation_required": True,
            "executed_nodes": ["compose_response"],
        }

    def audit_execution(state: AssistantState) -> dict[str, Any]:
        event = auditor.log(state)
        return {
            "run_id": event["run_id"],
            "audited_at": event["timestamp_utc"],
            "executed_nodes": ["audit_execution"],
        }

    builder = StateGraph(AssistantState)
    builder.add_node("validate_request", validate_request)
    builder.add_node("invalid_response", invalid_response)
    builder.add_node("blocked_response", blocked_response)
    builder.add_node("load_patient", load_patient)
    builder.add_node("not_found_response", not_found_response)
    builder.add_node("assess_patient", assess_patient)
    builder.add_node("emergency_response", emergency_response)
    builder.add_node("missing_data_response", missing_data_response)
    builder.add_node("retrieve_protocols", retrieve_protocols)
    builder.add_node("compose_response", compose_response)
    builder.add_node("audit_execution", audit_execution)

    builder.add_edge(START, "validate_request")
    builder.add_conditional_edges("validate_request", route_request)
    builder.add_conditional_edges("load_patient", route_patient)
    builder.add_conditional_edges("assess_patient", route_priority)
    builder.add_edge("retrieve_protocols", "compose_response")
    for terminal in (
        "invalid_response",
        "blocked_response",
        "not_found_response",
        "emergency_response",
        "missing_data_response",
        "compose_response",
    ):
        builder.add_edge(terminal, "audit_execution")
    builder.add_edge("audit_execution", END)

    return builder.compile()
