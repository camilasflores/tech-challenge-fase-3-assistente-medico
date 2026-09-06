"""Seleção do gerador a partir da configuração da aplicação."""

from __future__ import annotations

import os

from app.models.generator import SafeFallbackGenerator, TextGenerator
from app.models.hf_lora import HuggingFaceLoRAGenerator


def create_generator_from_environment() -> TextGenerator:
    """Usa o LoRA configurado ou retorna o fallback determinístico."""
    adapter_path = os.getenv("LORA_ADAPTER_PATH", "").strip()
    if not adapter_path:
        return SafeFallbackGenerator()
    return HuggingFaceLoRAGenerator(adapter_path)

