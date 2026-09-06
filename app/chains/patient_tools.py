"""Ferramentas LangChain para consultar dados estruturados do paciente."""

from __future__ import annotations

from pathlib import Path

from langchain.tools import tool

from app.database.repository import PatientRepository


def create_patient_tools(database_path: Path | None = None) -> list:
    """Cria tools ligadas a uma instância somente leitura do repositório."""
    repository = PatientRepository(database_path) if database_path else PatientRepository()

    @tool
    def get_patient_record(patient_id: str) -> dict:
        """Consulta o prontuário sintético completo pelo ID no formato PAC-000.

        Use quando a pergunta depender de sinais vitais, diagnósticos,
        medicamentos, sintomas, exames ou data do último acompanhamento.
        """
        record = repository.get_patient(patient_id)
        if record is None:
            return {
                "found": False,
                "patient_id": patient_id,
                "message": "Paciente sintético não encontrado.",
            }
        return {"found": True, "record": record, "source": "sqlite:medical_records"}

    @tool
    def get_pending_exams(patient_id: str) -> dict:
        """Lista exames pendentes de um paciente sintético pelo ID PAC-000.

        Use quando a pergunta mencionar pendências, exames não realizados ou
        acompanhamento incompleto.
        """
        try:
            exams = repository.get_pending_exams(patient_id)
        except LookupError as error:
            return {"found": False, "patient_id": patient_id, "message": str(error)}
        return {
            "found": True,
            "patient_id": patient_id.upper(),
            "pending_exams": exams,
            "count": len(exams),
            "source": "sqlite:exams",
        }

    return [get_patient_record, get_pending_exams]
