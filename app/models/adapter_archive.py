"""Validação e extração segura do ZIP exportado pelo notebook."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any
from zipfile import ZipFile


CONFIG_FILE = "adapter_config.json"
WEIGHT_FILES = ("adapter_model.safetensors", "adapter_model.bin")
OPTIONAL_FILES = (
    "tokenizer.json",
    "tokenizer_config.json",
    "chat_template.jinja",
    "README.md",
)


def inspect_adapter_archive(archive_path: Path | str) -> dict[str, Any]:
    """Confere os arquivos raiz sem carregar checkpoints ou objetos pickle."""
    path = Path(archive_path)
    with ZipFile(path) as archive:
        root_files = {
            info.filename: info.file_size
            for info in archive.infolist()
            if "/" not in info.filename.rstrip("/") and not info.is_dir()
        }
        if CONFIG_FILE not in root_files:
            raise ValueError(f"{CONFIG_FILE} não encontrado na raiz do ZIP.")
        weight_file = next(
            (name for name in WEIGHT_FILES if name in root_files), None
        )
        if weight_file is None:
            raise ValueError("Pesos do adaptador não encontrados na raiz do ZIP.")
        config = json.loads(archive.read(CONFIG_FILE).decode("utf-8"))

    if config.get("peft_type") != "LORA":
        raise ValueError("O arquivo não descreve um adaptador LoRA.")
    if config.get("task_type") != "CAUSAL_LM":
        raise ValueError("O adaptador não foi treinado para Causal LM.")
    return {
        "archive": path.name,
        "base_model": config.get("base_model_name_or_path"),
        "peft_version": config.get("peft_version"),
        "rank": config.get("r"),
        "lora_alpha": config.get("lora_alpha"),
        "weight_file": weight_file,
        "weight_size_bytes": root_files[weight_file],
        "available_root_files": sorted(root_files),
    }


def extract_inference_adapter(
    archive_path: Path | str, output_dir: Path | str
) -> list[Path]:
    """Extrai somente config, pesos e tokenizer presentes na raiz."""
    inspect_adapter_archive(archive_path)
    destination = Path(output_dir)
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"O diretório de saída não está vazio: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    extracted: list[Path] = []
    allowed = {CONFIG_FILE, *WEIGHT_FILES, *OPTIONAL_FILES}
    with ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        for filename in sorted(allowed & names):
            target = destination / filename
            with archive.open(filename) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            extracted.append(target)
    return extracted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    metadata = inspect_adapter_archive(args.archive)
    files = extract_inference_adapter(args.archive, args.output_dir)
    print(json.dumps({**metadata, "extracted": [str(item) for item in files]}, indent=2))


if __name__ == "__main__":
    main()

