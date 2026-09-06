"""Busca semântica nos protocolos internos fictícios do projeto."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROTOCOL_DIR = PROJECT_ROOT / "data" / "protocols"
DEFAULT_EMBEDDING_MODEL = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


def load_protocol_documents(
    protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
) -> list[Document]:
    """Carrega e fragmenta protocolos Markdown, preservando sua procedência."""
    directory = Path(protocol_dir)
    paths = sorted(directory.glob("*.md"))
    if not paths:
        raise FileNotFoundError(f"Nenhum protocolo Markdown encontrado em {directory}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )
    documents: list[Document] = []

    for path in paths:
        content = path.read_text(encoding="utf-8")
        first_line = content.splitlines()[0].removeprefix("# ").strip()
        chunks = splitter.split_text(content)

        for index, chunk in enumerate(chunks):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "protocol_id": path.stem,
                        "title": first_line,
                        "source": str(path.relative_to(PROJECT_ROOT)),
                        "chunk_index": index,
                    },
                )
            )

    return documents


def create_default_embeddings() -> Embeddings:
    """Cria embeddings multilíngues locais apenas quando a aplicação precisar."""
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=DEFAULT_EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def build_protocol_retriever(
    protocol_dir: Path | str = DEFAULT_PROTOCOL_DIR,
    embeddings: Embeddings | None = None,
    *,
    k: int = 3,
) -> Any:
    """Indexa os protocolos e devolve um retriever LangChain."""
    if k < 1:
        raise ValueError("k deve ser maior ou igual a 1")

    embedding_model = embeddings or create_default_embeddings()
    vector_store = InMemoryVectorStore(embedding=embedding_model)
    vector_store.add_documents(load_protocol_documents(protocol_dir))
    return vector_store.as_retriever(search_kwargs={"k": k})

