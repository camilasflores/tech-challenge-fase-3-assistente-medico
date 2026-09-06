"""Entrada de linha de comando para demonstrar o fluxo do assistente."""

from __future__ import annotations

import argparse
import json

from app.database.seed import DEFAULT_DATABASE, seed_database
from app.graph.workflow import build_assistant_graph


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("patient_id", help="Identificador sintético, por exemplo PAC-003")
    parser.add_argument("question", help="Pergunta para o assistente acadêmico")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not DEFAULT_DATABASE.exists():
        seed_database(DEFAULT_DATABASE)

    graph = build_assistant_graph()
    result = graph.invoke(
        {"patient_id": args.patient_id, "question": args.question}
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

