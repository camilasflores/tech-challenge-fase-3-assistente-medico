from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from langchain_core.documents import Document

from app.database.repository import PatientRepository
from app.database.seed import seed_database
from app.graph.workflow import build_assistant_graph
from app.observability.audit import AuditLogger


class StubProtocolRetriever:
    def invoke(self, query: str) -> list[Document]:
        return [
            Document(
                page_content="Apresentar medidas registradas e exigir revisão humana.",
                metadata={
                    "protocol_id": "PROTOCOLO_HAS_001",
                    "title": "Acompanhamento de hipertensão",
                    "source": "data/protocols/PROTOCOLO_HAS_001.md",
                    "chunk_index": 1,
                },
            )
        ]


class SafeStubGenerator:
    model_name = "safe_stub"

    def generate(self, messages: list[dict[str, str]]) -> str:
        return (
            "Exames pendentes: creatinina, glicemia de jejum e perfil lipidico. "
            "A validação por profissional habilitado é obrigatória."
        )


class UnsafeStubGenerator:
    model_name = "unsafe_stub"

    def generate(self, messages: list[dict[str, str]]) -> str:
        return "Tome losartana todos os dias."


@pytest.fixture
def graph():
    with tempfile.TemporaryDirectory() as directory:
        database_path = Path(directory) / "test.db"
        seed_database(database_path)
        yield build_assistant_graph(
            repository=PatientRepository(database_path),
            protocol_retriever=StubProtocolRetriever(),
            audit_logger=AuditLogger(Path(directory) / "audit.jsonl"),
            text_generator=SafeStubGenerator(),
        )


def test_blocks_prohibited_request_before_loading_patient(graph):
    result = graph.invoke({"question": "Qual medicamento você recomenda?", "patient_id": "PAC-002"})

    assert result["blocked"] is True
    assert result["priority"] == "bloqueado"
    assert "load_patient" not in result["executed_nodes"]
    assert result["sources"] == ["data/protocols/POLITICA_SEGURANCA_001.md"]
    assert result["executed_nodes"][-1] == "audit_execution"
    assert result["run_id"]


def test_interrupts_common_flow_for_emergency(graph):
    result = graph.invoke({"question": "Resuma o acompanhamento", "patient_id": "PAC-004"})

    assert result["priority"] == "revisao_imediata"
    assert "REVISÃO IMEDIATA" in result["final_answer"]
    assert "retrieve_protocols" not in result["executed_nodes"]
    assert result["human_validation_required"] is True


def test_requests_missing_patient_data_without_inventing(graph):
    result = graph.invoke({"question": "Resuma o acompanhamento", "patient_id": "PAC-005"})

    assert result["priority"] == "dados_insuficientes"
    assert "latest_vitals" in result["missing_fields"]
    assert "compose_response" not in result["executed_nodes"]


def test_common_flow_retrieves_protocol_and_composes_traceable_answer(graph):
    result = graph.invoke({"question": "Quais exames estão pendentes?", "patient_id": "PAC-003"})

    assert result["priority"] == "revisao_clinica"
    assert result["executed_nodes"] == [
        "validate_request",
        "load_patient",
        "assess_patient",
        "retrieve_protocols",
        "compose_response",
        "audit_execution",
    ]
    assert "perfil lipidico" in result["final_answer"]
    assert "sqlite:medical_records" in result["sources"]
    assert "data/protocols/PROTOCOLO_HAS_001.md" in result["sources"]
    assert result["model_name"] == "safe_stub"
    assert result["generation_fallback"] is False


def test_unsafe_model_output_is_replaced_by_deterministic_fallback():
    with tempfile.TemporaryDirectory() as directory:
        database_path = Path(directory) / "test.db"
        seed_database(database_path)
        graph = build_assistant_graph(
            repository=PatientRepository(database_path),
            protocol_retriever=StubProtocolRetriever(),
            audit_logger=AuditLogger(Path(directory) / "audit.jsonl"),
            text_generator=UnsafeStubGenerator(),
        )

        result = graph.invoke(
            {"question": "Quais exames estão pendentes?", "patient_id": "PAC-003"}
        )

    assert result["generation_fallback"] is True
    assert result["model_name"] == "unsafe_stub"
    assert "Tome losartana" not in result["final_answer"]
    assert "validação por profissional habilitado" in result["final_answer"]


def test_rejects_invalid_identifier(graph):
    result = graph.invoke({"question": "Mostre o prontuário", "patient_id": "PAC-001' OR 1=1"})

    assert result["blocked"] is True
    assert result["executed_nodes"] == [
        "validate_request",
        "invalid_response",
        "audit_execution",
    ]
    assert "formato sintético" in result["final_answer"]
