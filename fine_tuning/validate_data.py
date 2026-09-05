"""Valida a estrutura e o caráter sintético dos dados iniciais."""

from __future__ import annotations

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PATIENTS_FILE = PROJECT_ROOT / "data" / "synthetic" / "patients.json"
FAQ_FILE = PROJECT_ROOT / "data" / "raw" / "internal_faq.jsonl"

REQUIRED_PATIENT_FIELDS = {
    "patient_id",
    "demographics",
    "diagnoses",
    "allergies",
    "medications",
    "latest_vitals",
    "reported_symptoms",
    "exams",
    "last_follow_up",
    "notes",
}

PROHIBITED_PATTERNS = {
    "cpf": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?55\s*)?\(?\d{2}\)?\s*9?\d{4}[-\s]?\d{4}\b"),
}


def load_json(path: Path) -> dict:
    """Carrega um arquivo JSON UTF-8."""
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def validate_patients() -> int:
    """Valida metadados, campos obrigatórios e IDs dos pacientes."""
    payload = load_json(PATIENTS_FILE)
    if payload.get("metadata", {}).get("synthetic") is not True:
        raise ValueError("O dataset deve estar explicitamente marcado como sintético.")

    patients = payload.get("patients", [])
    if not patients:
        raise ValueError("O dataset não contém pacientes.")

    ids: set[str] = set()
    for patient in patients:
        missing = REQUIRED_PATIENT_FIELDS - patient.keys()
        if missing:
            raise ValueError(
                f"Paciente {patient.get('patient_id', '<sem id>')} sem campos: "
                f"{sorted(missing)}"
            )

        patient_id = patient["patient_id"]
        if patient_id in ids:
            raise ValueError(f"ID duplicado: {patient_id}")
        if not re.fullmatch(r"PAC-\d{3}", patient_id):
            raise ValueError(f"ID fora do padrão sintético: {patient_id}")
        ids.add(patient_id)

    return len(patients)


def validate_privacy() -> None:
    """Busca formatos comuns de identificadores pessoais nos arquivos de dados."""
    for path in (PATIENTS_FILE, FAQ_FILE):
        content = path.read_text(encoding="utf-8")
        for label, pattern in PROHIBITED_PATTERNS.items():
            if pattern.search(content):
                raise ValueError(f"Possível {label} encontrado em {path}")


def validate_faq() -> int:
    """Valida o JSONL de perguntas e respostas internas."""
    records = []
    with FAQ_FILE.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            record = json.loads(line)
            required = {"id", "category", "question", "answer"}
            missing = required - record.keys()
            if missing:
                raise ValueError(f"FAQ linha {line_number} sem campos: {sorted(missing)}")
            records.append(record)

    if len({record["id"] for record in records}) != len(records):
        raise ValueError("Existem IDs duplicados no FAQ.")
    return len(records)


def main() -> None:
    """Executa todas as validações e exibe um resumo."""
    patient_count = validate_patients()
    faq_count = validate_faq()
    validate_privacy()
    print(f"Dados válidos: {patient_count} pacientes e {faq_count} FAQs.")


if __name__ == "__main__":
    main()
