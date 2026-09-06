"""Consultas somente leitura aos prontuários sintéticos."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

from app.database.seed import DEFAULT_DATABASE


PATIENT_ID_PATTERN = re.compile(r"PAC-\d{3}")


class PatientRepository:
    """Fornece consultas parametrizadas sem expor SQL à LLM."""

    def __init__(self, database_path: Path = DEFAULT_DATABASE) -> None:
        self.database_path = Path(database_path)

    def _connect(self) -> sqlite3.Connection:
        if not self.database_path.exists():
            raise FileNotFoundError(
                "Banco não encontrado. Execute: python -m app.database.seed"
            )
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _validate_patient_id(patient_id: str) -> str:
        normalized = patient_id.strip().upper()
        if not PATIENT_ID_PATTERN.fullmatch(normalized):
            raise ValueError("patient_id deve seguir o formato sintético PAC-000.")
        return normalized

    @staticmethod
    def _rows(connection: sqlite3.Connection, query: str, params: tuple) -> list[dict]:
        return [dict(row) for row in connection.execute(query, params).fetchall()]

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        """Retorna o prontuário estruturado ou None quando o ID não existe."""
        patient_id = self._validate_patient_id(patient_id)
        with self._connect() as connection:
            patient_row = connection.execute(
                """
                SELECT patient_id, age, sex, last_follow_up, notes
                FROM patients WHERE patient_id = ?
                """,
                (patient_id,),
            ).fetchone()
            if patient_row is None:
                return None

            vitals = connection.execute(
                """
                SELECT measured_at, systolic_bp, diastolic_bp, heart_rate
                FROM vitals WHERE patient_id = ? ORDER BY measured_at DESC LIMIT 1
                """,
                (patient_id,),
            ).fetchone()
            return {
                **dict(patient_row),
                "diagnoses": [
                    row["diagnosis"]
                    for row in connection.execute(
                        "SELECT diagnosis FROM diagnoses WHERE patient_id = ? ORDER BY diagnosis",
                        (patient_id,),
                    )
                ],
                "allergies": [
                    row["allergy"]
                    for row in connection.execute(
                        "SELECT allergy FROM allergies WHERE patient_id = ? ORDER BY allergy",
                        (patient_id,),
                    )
                ],
                "medications": self._rows(
                    connection,
                    """
                    SELECT name, dose, frequency FROM medications
                    WHERE patient_id = ? ORDER BY name
                    """,
                    (patient_id,),
                ),
                "latest_vitals": dict(vitals) if vitals else None,
                "reported_symptoms": [
                    row["symptom"]
                    for row in connection.execute(
                        "SELECT symptom FROM symptoms WHERE patient_id = ? ORDER BY symptom",
                        (patient_id,),
                    )
                ],
                "exams": self._rows(
                    connection,
                    """
                    SELECT name, status, exam_date AS date, due_date, result
                    FROM exams WHERE patient_id = ? ORDER BY name
                    """,
                    (patient_id,),
                ),
            }

    def get_pending_exams(self, patient_id: str) -> list[dict[str, Any]]:
        """Lista apenas exames explicitamente registrados como pendentes."""
        patient_id = self._validate_patient_id(patient_id)
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM patients WHERE patient_id = ?", (patient_id,)
            ).fetchone()
            if exists is None:
                raise LookupError(f"Paciente sintético não encontrado: {patient_id}")
            return self._rows(
                connection,
                """
                SELECT name, due_date FROM exams
                WHERE patient_id = ? AND status = 'pending'
                ORDER BY due_date, name
                """,
                (patient_id,),
            )
