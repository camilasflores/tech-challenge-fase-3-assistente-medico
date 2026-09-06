import json

import pytest

from app.models.factory import create_generator_from_environment
from app.models.generator import SafeFallbackGenerator
from app.models.hf_lora import HuggingFaceLoRAGenerator


def test_factory_uses_safe_fallback_without_adapter(monkeypatch):
    monkeypatch.delenv("LORA_ADAPTER_PATH", raising=False)

    generator = create_generator_from_environment()

    assert isinstance(generator, SafeFallbackGenerator)


def test_lora_loader_validates_required_files_without_loading_model(tmp_path):
    (tmp_path / "adapter_config.json").write_text(
        json.dumps(
            {"base_model_name_or_path": "Qwen/Qwen2.5-1.5B-Instruct"}
        ),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError, match="pesos"):
        HuggingFaceLoRAGenerator(tmp_path)


def test_lora_loader_reads_base_model_from_adapter_config(tmp_path):
    (tmp_path / "adapter_config.json").write_text(
        json.dumps(
            {"base_model_name_or_path": "Qwen/Qwen2.5-1.5B-Instruct"}
        ),
        encoding="utf-8",
    )
    (tmp_path / "adapter_model.safetensors").touch()

    generator = HuggingFaceLoRAGenerator(tmp_path)

    assert generator._base_model_id() == "Qwen/Qwen2.5-1.5B-Instruct"
