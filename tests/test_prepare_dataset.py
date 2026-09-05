import json
import tempfile
import unittest
from pathlib import Path

from fine_tuning.prepare_dataset import (
    anonymize_text,
    build_examples,
    prepare_dataset,
    read_jsonl,
)


class PrepareDatasetTest(unittest.TestCase):
    def test_anonymizes_common_personal_identifiers(self) -> None:
        text = (
            "Paciente Maria Silva, CPF 123.456.789-00, telefone (11) 98765-4321 "
            "e e-mail maria@example.com."
        )
        result = anonymize_text(text)
        self.assertNotIn("Maria Silva", result)
        self.assertNotIn("123.456.789-00", result)
        self.assertNotIn("98765-4321", result)
        self.assertNotIn("maria@example.com", result)
        self.assertIn("[NOME_REMOVIDO]", result)
        self.assertIn("[CPF_REMOVIDO]", result)

    def test_builds_three_variants_per_record(self) -> None:
        records = [
            {"id": "FAQ-001", "category": "teste", "question": "Posso ajudar?", "answer": "Sim."}
        ]
        examples = build_examples(records)
        self.assertEqual(len(examples), 3)
        self.assertEqual(examples[0]["messages"][0]["role"], "system")
        self.assertEqual(examples[0]["messages"][2]["role"], "assistant")

    def test_split_has_no_source_leakage(self) -> None:
        input_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "internal_faq.jsonl"
        with tempfile.TemporaryDirectory() as temp_dir:
            report = prepare_dataset(input_path, Path(temp_dir))
            for overlap in report["source_overlap"].values():
                self.assertEqual(overlap, [])
            self.assertEqual(report["total_examples"], 60)
            self.assertEqual(report["examples_per_split"]["train"], 42)
            self.assertEqual(report["examples_per_split"]["validation"], 9)
            self.assertEqual(report["examples_per_split"]["test"], 9)

            written = read_jsonl(Path(temp_dir) / "train.jsonl")
            self.assertEqual(len(written), report["examples_per_split"]["train"])
            json.dumps(written, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
