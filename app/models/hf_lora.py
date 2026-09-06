"""Inferência local com o modelo Qwen base e o adaptador LoRA treinado."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models.generator import ChatMessage


class HuggingFaceLoRAGenerator:
    """Carrega modelo e adaptador sob demanda para não pesar os imports."""

    def __init__(self, adapter_path: Path | str, *, max_new_tokens: int = 220) -> None:
        self.adapter_path = Path(adapter_path)
        self.max_new_tokens = max_new_tokens
        self.model_name = "qwen2.5-1.5b-instruct+lora"
        self._model: Any | None = None
        self._tokenizer: Any | None = None
        self._validate_adapter()

    def _validate_adapter(self) -> None:
        if not self.adapter_path.is_dir():
            raise FileNotFoundError(
                f"Diretório do adaptador não encontrado: {self.adapter_path}"
            )
        if not (self.adapter_path / "adapter_config.json").is_file():
            raise FileNotFoundError("O adaptador não contém adapter_config.json.")
        has_weights = any(
            (self.adapter_path / filename).is_file()
            for filename in ("adapter_model.safetensors", "adapter_model.bin")
        )
        if not has_weights:
            raise FileNotFoundError(
                "Os pesos adapter_model.safetensors/bin não foram encontrados."
            )

    def _base_model_id(self) -> str:
        config = json.loads(
            (self.adapter_path / "adapter_config.json").read_text(encoding="utf-8")
        )
        model_id = config.get("base_model_name_or_path")
        if not model_id:
            raise ValueError(
                "base_model_name_or_path ausente no adapter_config.json."
            )
        return model_id

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return

        import torch
        from peft import PeftModel
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer

        base_model_id = self._base_model_id()
        tokenizer_source = (
            self.adapter_path
            if (self.adapter_path / "tokenizer_config.json").is_file()
            else base_model_id
        )
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_source)
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        dtype_argument = (
            {"dtype": dtype}
            if int(transformers.__version__.split(".", 1)[0]) >= 5
            else {"torch_dtype": dtype}
        )
        model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            device_map="auto",
            low_cpu_mem_usage=True,
            **dtype_argument,
        )
        model = PeftModel.from_pretrained(model, self.adapter_path)
        model.eval()
        self._tokenizer = tokenizer
        self._model = model

    def generate(self, messages: list[ChatMessage]) -> str:
        self._ensure_loaded()
        import torch

        encoded = self._tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        )
        encoded = {
            key: value.to(self._model.device) for key, value in encoded.items()
        }
        prompt_length = encoded["input_ids"].shape[-1]
        with torch.inference_mode():
            output = self._model.generate(
                **encoded,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=self._tokenizer.pad_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
            )
        return self._tokenizer.decode(
            output[0][prompt_length:], skip_special_tokens=True
        ).strip()
