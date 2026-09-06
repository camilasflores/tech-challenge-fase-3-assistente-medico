import json
from zipfile import ZipFile

import pytest

from app.models.adapter_archive import (
    extract_inference_adapter,
    inspect_adapter_archive,
)


def create_adapter_zip(path, *, include_weights=True):
    config = {
        "base_model_name_or_path": "Qwen/Qwen2.5-1.5B-Instruct",
        "peft_type": "LORA",
        "task_type": "CAUSAL_LM",
        "peft_version": "0.20.0",
        "r": 16,
        "lora_alpha": 32,
    }
    with ZipFile(path, "w") as archive:
        archive.writestr("adapter_config.json", json.dumps(config))
        archive.writestr("tokenizer_config.json", "{}")
        archive.writestr("checkpoint-24/optimizer.pt", b"do-not-extract")
        if include_weights:
            archive.writestr("adapter_model.safetensors", b"fake-safe-weights")


def test_inspects_root_adapter_metadata(tmp_path):
    archive_path = tmp_path / "adapter.zip"
    create_adapter_zip(archive_path)

    metadata = inspect_adapter_archive(archive_path)

    assert metadata["base_model"] == "Qwen/Qwen2.5-1.5B-Instruct"
    assert metadata["rank"] == 16
    assert metadata["weight_file"] == "adapter_model.safetensors"


def test_extracts_only_inference_files_and_ignores_checkpoints(tmp_path):
    archive_path = tmp_path / "adapter.zip"
    output_dir = tmp_path / "adapter"
    create_adapter_zip(archive_path)

    extracted = extract_inference_adapter(archive_path, output_dir)

    assert {item.name for item in extracted} == {
        "adapter_config.json",
        "adapter_model.safetensors",
        "tokenizer_config.json",
    }
    assert not (output_dir / "checkpoint-24").exists()


def test_rejects_archive_without_adapter_weights(tmp_path):
    archive_path = tmp_path / "adapter.zip"
    create_adapter_zip(archive_path, include_weights=False)

    with pytest.raises(ValueError, match="Pesos"):
        inspect_adapter_archive(archive_path)

