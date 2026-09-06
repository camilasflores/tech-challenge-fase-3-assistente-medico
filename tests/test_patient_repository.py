import tempfile
import unittest
from pathlib import Path

from app.database.repository import PatientRepository
from app.database.seed import seed_database


class PatientRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        seed_database(self.database_path)
        self.repository = PatientRepository(self.database_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_creates_database_with_five_patients(self) -> None:
        self.assertTrue(self.database_path.exists())
        self.assertIsNotNone(self.repository.get_patient("PAC-005"))

    def test_returns_complete_patient_record(self) -> None:
        patient = self.repository.get_patient("pac-002")
        self.assertEqual(patient["patient_id"], "PAC-002")
        self.assertEqual(patient["latest_vitals"]["systolic_bp"], 164)
        self.assertIn("diabetes mellitus tipo 2", patient["diagnoses"])
        self.assertEqual(len(patient["medications"]), 2)

    def test_lists_only_pending_exams(self) -> None:
        exams = self.repository.get_pending_exams("PAC-003")
        self.assertEqual(len(exams), 3)
        self.assertTrue(all(exam["due_date"] == "2026-08-01" for exam in exams))

    def test_patient_without_vitals_preserves_missing_value(self) -> None:
        patient = self.repository.get_patient("PAC-005")
        self.assertIsNone(patient["latest_vitals"])
        self.assertEqual(patient["exams"], [])

    def test_unknown_patient_returns_none(self) -> None:
        self.assertIsNone(self.repository.get_patient("PAC-999"))

    def test_rejects_invalid_identifier_instead_of_running_free_sql(self) -> None:
        with self.assertRaises(ValueError):
            self.repository.get_patient("PAC-001' OR 1=1 --")


if __name__ == "__main__":
    unittest.main()
