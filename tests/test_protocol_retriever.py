from __future__ import annotations

import hashlib

import pytest
from langchain_core.embeddings import Embeddings

from app.chains.protocol_retriever import (
    DEFAULT_PROTOCOL_DIR,
    build_protocol_retriever,
    load_protocol_documents,
)


class DeterministicEmbeddings(Embeddings):
    """Embedding leve para testar o encadeamento sem baixar um modelo."""

    dimensions = 32

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for word in text.casefold().split():
            digest = hashlib.sha256(word.encode("utf-8")).digest()
            vector[digest[0] % self.dimensions] += 1.0
        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def test_load_protocol_documents_preserves_sources():
    documents = load_protocol_documents()

    protocol_ids = {document.metadata["protocol_id"] for document in documents}
    assert protocol_ids == {"POLITICA_SEGURANCA_001", "PROTOCOLO_HAS_001"}
    assert all(document.metadata["source"].startswith("data/protocols/") for document in documents)
    assert all(document.page_content.strip() for document in documents)


def test_retriever_returns_documents_with_traceability():
    retriever = build_protocol_retriever(
        DEFAULT_PROTOCOL_DIR,
        embeddings=DeterministicEmbeddings(),
        k=2,
    )

    results = retriever.invoke("medicamento dose ação proibida")

    assert len(results) == 2
    assert all("protocol_id" in document.metadata for document in results)
    assert all("source" in document.metadata for document in results)


def test_retriever_rejects_invalid_k():
    with pytest.raises(ValueError, match="k deve ser"):
        build_protocol_retriever(embeddings=DeterministicEmbeddings(), k=0)

