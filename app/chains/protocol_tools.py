"""Ferramentas LangChain para consultar protocolos internos."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool, tool

from app.chains.protocol_retriever import build_protocol_retriever


def create_protocol_tools(retriever: Any | None = None) -> list[BaseTool]:
    """Cria a ferramenta de RAG com retriever injetável para facilitar testes."""
    protocol_retriever = retriever or build_protocol_retriever()

    @tool
    def search_internal_protocols(query: str) -> dict[str, Any]:
        """Busca orientações e limites nos protocolos internos fictícios."""
        if not query.strip():
            raise ValueError("A consulta ao protocolo não pode ser vazia")

        documents = protocol_retriever.invoke(query)
        excerpts = [
            {
                "content": document.page_content,
                "protocol_id": document.metadata["protocol_id"],
                "title": document.metadata["title"],
                "source": document.metadata["source"],
                "chunk_index": document.metadata["chunk_index"],
            }
            for document in documents
        ]
        return {
            "query": query,
            "result_count": len(excerpts),
            "excerpts": excerpts,
            "notice": "Conteúdo fictício; exige validação por profissional habilitado.",
        }

    return [search_internal_protocols]

