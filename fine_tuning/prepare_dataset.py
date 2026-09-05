"""Prepara o dataset de instruções usado no fine-tuning supervisionado."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "internal_faq.jsonl"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed"
RANDOM_SEED = 42

SYSTEM_PROMPT = (
    "Você é um assistente acadêmico de apoio à equipe médica. Responda apenas "
    "com base nos protocolos fornecidos, não faça diagnóstico nem prescrição, "
    "não invente dados ausentes e indique quando a validação humana é necessária."
)

QUESTION_TEMPLATES = (
    "{question}",
    "Segundo o protocolo interno, {question_lower}",
    "Preciso de apoio para esta dúvida: {question_lower}",
)

SENSITIVE_PATTERNS = (
    (re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"), "[CPF_REMOVIDO]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REMOVIDO]"),
    (
        re.compile(r"\b(?:\+?55\s*)?\(?\d{2}\)?\s*9?\d{4}[-\s]?\d{4}\b"),
        "[TELEFONE_REMOVIDO]",
    ),
    (
        re.compile(
            r"\b(?:paciente|sr\.?|sra\.?)\s+"
            r"[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-Za-zÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇáàâãéèêíìîóòôõúùûç]+"
            r"(?:\s+[A-ZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ][A-Za-zÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇáàâãéèêíìîóòôõúùûç]+){0,3}",
            flags=re.IGNORECASE,
        ),
        "paciente [NOME_REMOVIDO]",
    ),
)


def normalize_text(value: str) -> str:
    """Normaliza Unicode e espaços sem remover acentos relevantes em português."""
    normalized = unicodedata.normalize("NFKC", value)
    return re.sub(r"\s+", " ", normalized).strip()


def anonymize_text(value: str) -> str:
    """Substitui formatos comuns de identificadores por marcadores explícitos."""
    result = normalize_text(value)
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def read_jsonl(path: Path) -> list[dict]:
    """Lê registros JSONL e informa a linha em caso de erro."""
    records = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"JSON inválido na linha {line_number} de {path}") from error
    return records


def build_examples(records: Iterable[dict]) -> list[dict]:
    """Converte FAQs em conversas e cria paráfrases controladas das perguntas."""
    examples = []
    for record in records:
        question = anonymize_text(record["question"])
        answer = anonymize_text(record["answer"])

        for variant, template in enumerate(QUESTION_TEMPLATES, start=1):
            user_text = template.format(
                question=question,
                question_lower=question[0].lower() + question[1:],
            )
            examples.append(
                {
                    "example_id": f"{record['id']}-V{variant}",
                    "source_id": record["id"],
                    "category": record["category"],
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_text},
                        {"role": "assistant", "content": answer},
                    ],
                }
            )
    return examples


def split_source_ids(source_ids: list[str]) -> dict[str, set[str]]:
    """Divide IDs de origem antes das variações para impedir vazamento."""
    unique_ids = sorted(set(source_ids))
    random.Random(RANDOM_SEED).shuffle(unique_ids)
    total = len(unique_ids)
    train_end = max(1, round(total * 0.7))
    validation_end = min(total - 1, train_end + max(1, round(total * 0.2)))
    return {
        "train": set(unique_ids[:train_end]),
        "validation": set(unique_ids[train_end:validation_end]),
        "test": set(unique_ids[validation_end:]),
    }


def split_examples(examples: list[dict]) -> dict[str, list[dict]]:
    """Distribui exemplos conforme a divisão dos respectivos IDs de origem."""
    source_splits = split_source_ids([example["source_id"] for example in examples])
    result = {split: [] for split in source_splits}
    for example in examples:
        for split, ids in source_splits.items():
            if example["source_id"] in ids:
                result[split].append(example)
                break
    return result


def write_jsonl(path: Path, records: Iterable[dict]) -> None:
    """Grava os registros em JSONL UTF-8."""
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def content_fingerprint(examples: Iterable[dict]) -> str:
    """Calcula hash reproduzível para auditoria da versão preparada."""
    serialized = json.dumps(list(examples), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def prepare_dataset(input_path: Path, output_dir: Path) -> dict:
    """Executa preparação, divisão, escrita e geração do relatório de qualidade."""
    raw_records = read_jsonl(input_path)
    examples = build_examples(raw_records)
    splits = split_examples(examples)

    output_dir.mkdir(parents=True, exist_ok=True)
    for split, split_records in splits.items():
        write_jsonl(output_dir / f"{split}.jsonl", split_records)

    split_source_ids = {
        split: sorted({record["source_id"] for record in records})
        for split, records in splits.items()
    }
    overlap = {
        "train_validation": sorted(
            set(split_source_ids["train"]) & set(split_source_ids["validation"])
        ),
        "train_test": sorted(
            set(split_source_ids["train"]) & set(split_source_ids["test"])
        ),
        "validation_test": sorted(
            set(split_source_ids["validation"]) & set(split_source_ids["test"])
        ),
    }
    report = {
        "dataset_version": "1.0.0",
        "random_seed": RANDOM_SEED,
        "raw_records": len(raw_records),
        "total_examples": len(examples),
        "examples_per_split": {split: len(records) for split, records in splits.items()},
        "source_ids_per_split": split_source_ids,
        "source_overlap": overlap,
        "categories": dict(sorted(Counter(item["category"] for item in examples).items())),
        "sha256": content_fingerprint(examples),
    }
    (output_dir / "quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = prepare_dataset(args.input, args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
