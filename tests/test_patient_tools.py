import tempfile
import unittest
from pathlib import Path

from app.chains.patient_tools import create_patient_tools
from app.database.seed import seed_database


class PatientToolsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "tools.db"
        seed_database(self.database_path)
        self.tools = {tool.name: tool for tool in create_patient_tools(self.database_path)}

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_exposes_expected_tool_names(self) -> None:
        self.assertEqual(set(self.tools), {"get_patient_record", "get_pending_exams"})

    def test_patient_tool_returns_structured_record_and_source(self) -> None:
        result = self.tools["get_patient_record"].invoke({"patient_id": "PAC-001"})
        self.assertTrue(result["found"])
        self.assertEqual(result["record"]["patient_id"], "PAC-001")
        self.assertEqual(result["source"], "sqlite:medical_records")

    def test_pending_exams_tool_returns_count(self) -> None:
        result = self.tools["get_pending_exams"].invoke({"patient_id": "PAC-002"})
        self.assertTrue(result["found"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["source"], "sqlite:exams")


if __name__ == "__main__":
    unittest.main()
