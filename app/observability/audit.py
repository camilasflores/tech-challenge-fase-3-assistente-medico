"""Registro mínimo e estruturado das execuções do assistente."""

from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT_LOG = PROJECT_ROOT / "artifacts" / "audit.jsonl"
VALID_PATIENT_ID = re.compile(r"PAC-\d{3}")


class AuditLogger:
    """Grava um evento JSON por linha, sem texto clínico livre."""

    def __init__(self, log_path: Path | str = DEFAULT_AUDIT_LOG) -> None:
        self.log_path = Path(log_path)
        self._lock = threading.Lock()

    @staticmethod
    def _triggered_rules(state: Mapping[str, Any]) -> list[str]:
        rules: list[str] = []
        if state.get("request_status") == "invalid":
            rules.append("invalid_input")
        if state.get("request_status") == "prohibited":
            rules.append("prohibited_action")
        if state.get("priority") == "revisao_imediata":
            rules.append("emergency_symptoms")
        if state.get("priority") == "dados_insuficientes":
            rules.append("missing_required_data")
        if "not_found_response" in state.get("executed_nodes", []):
            rules.append("patient_not_found")
        return rules

    def log(self, state: Mapping[str, Any]) -> dict[str, Any]:
        """Persiste metadados permitidos e devolve o evento registrado."""
        raw_patient_id = state.get("patient_id", "")
        patient_id = raw_patient_id if VALID_PATIENT_ID.fullmatch(raw_patient_id) else None
        event = {
            "run_id": str(uuid.uuid4()),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "patient_id": patient_id,
            "request_status": state.get("request_status"),
            "priority": state.get("priority"),
            "blocked": bool(state.get("blocked")),
            "human_validation_required": bool(
                state.get("human_validation_required")
            ),
            "model_name": state.get("model_name"),
            "generation_fallback": state.get("generation_fallback"),
            "executed_nodes": [*state.get("executed_nodes", []), "audit_execution"],
            "sources": list(dict.fromkeys(state.get("sources", []))),
            "triggered_rules": self._triggered_rules(state),
        }

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(event, ensure_ascii=False, sort_keys=True)
        with self._lock, self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(serialized + "\n")
        return event
