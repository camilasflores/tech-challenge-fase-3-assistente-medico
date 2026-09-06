"""Contrato de geração e implementação segura sem LoRA."""

from __future__ import annotations

from typing import Protocol


ChatMessage = dict[str, str]


class TextGenerator(Protocol):
    model_name: str

    def generate(self, messages: list[ChatMessage]) -> str:
        """Gera uma resposta a partir de mensagens no formato de chat."""


class SafeFallbackGenerator:
    """Resposta previsível quando nenhum adaptador foi configurado."""

    model_name = "safe_fallback"

    def generate(self, messages: list[ChatMessage]) -> str:
        return (
            "Os dados foram organizados para apoio à análise. A interpretação "
            "e qualquer conduta exigem validação por profissional habilitado."
        )

