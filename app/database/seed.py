"""Cria e popula o SQLite a partir dos prontuários sintéticos versionados."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "synthetic" / "patients.json"
DEFAULT_DATABASE = PROJECT_ROOT / "artifacts" / "medical_records.db"
SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def load_patients(source_path: Path) -> list[dict]:
    """Carrega somente datasets explicitamente marcados como sintéticos."""
    with source_path.open(encoding="utf-8") as file:
        payload = json.load(file)
    if payload.get("metadata", {}).get("synthetic") is not True:
        raise ValueError("A origem precisa estar marcada como dataset sintético.")
    return payload["patients"]


def seed_database(database_path: Path, source_path: Path = DEFAULT_SOURCE) -> int:
    """Recria o banco e retorna a quantidade de pacientes inseridos."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()

    patients = load_patients(source_path)
    schema = SCHEMA_FILE.read_text(encoding="utf-8")

    with sqlite3.connect(database_path) as connection:
        connection.executescript(schema)
        for patient in patients:
            demographics = patient["demographics"]
            connection.execute(
                """
                INSERT INTO patients (patient_id, age, sex, last_follow_up, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    patient["patient_id"],
                    demographics["age"],
                    demographics["sex"],
                    patient["last_follow_up"],
                    patient["notes"],
                ),
            )
            connection.executemany(
                "INSERT INTO diagnoses (patient_id, diagnosis) VALUES (?, ?)",
                [(patient["patient_id"], item) for item in patient["diagnoses"]],
            )
            connection.executemany(
                "INSERT INTO allergies (patient_id, allergy) VALUES (?, ?)",
                [(patient["patient_id"], item) for item in patient["allergies"]],
            )
            connection.executemany(
                """
                INSERT INTO medications (patient_id, name, dose, frequency)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        patient["patient_id"],
                        item["name"],
                        item["dose"],
                        item["frequency"],
                    )
                    for item in patient["medications"]
                ],
            )
            if patient["latest_vitals"]:
                vitals = patient["latest_vitals"]
                connection.execute(
                    """
                    INSERT INTO vitals (
                        patient_id, measured_at, systolic_bp, diastolic_bp, heart_rate
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        patient["patient_id"],
                        vitals["measured_at"],
                        vitals["systolic_bp"],
                        vitals["diastolic_bp"],
                        vitals["heart_rate"],
                    ),
                )
            connection.executemany(
                "INSERT INTO symptoms (patient_id, symptom) VALUES (?, ?)",
                [(patient["patient_id"], item) for item in patient["reported_symptoms"]],
            )
            connection.executemany(
                """
                INSERT INTO exams (
                    patient_id, name, status, exam_date, due_date, result
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        patient["patient_id"],
                        item["name"],
                        item["status"],
                        item.get("date"),
                        item.get("due_date"),
                        item.get("result"),
                    )
                    for item in patient["exams"]
                ],
            )
    return len(patients)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = seed_database(args.database, args.source)
    print(f"Banco criado em {args.database} com {count} pacientes sintéticos.")


if __name__ == "__main__":
    main()
