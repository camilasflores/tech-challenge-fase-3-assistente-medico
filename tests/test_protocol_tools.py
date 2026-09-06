from langchain_core.documents import Document

from app.chains.protocol_tools import create_protocol_tools


class StubRetriever:
    def invoke(self, query: str) -> list[Document]:
        return [
            Document(
                page_content="O assistente não pode ajustar medicamentos e doses.",
                metadata={
                    "protocol_id": "POLITICA_SEGURANCA_001",
                    "title": "Limites do assistente médico",
                    "source": "data/protocols/POLITICA_SEGURANCA_001.md",
                    "chunk_index": 1,
                },
            )
        ]


def test_protocol_tool_returns_excerpt_and_citation():
    tool = create_protocol_tools(StubRetriever())[0]

    result = tool.invoke({"query": "Pode ajustar a dose?"})

    assert result["result_count"] == 1
    assert result["excerpts"][0]["protocol_id"] == "POLITICA_SEGURANCA_001"
    assert result["excerpts"][0]["source"].endswith("POLITICA_SEGURANCA_001.md")
    assert "validação" in result["notice"]


def test_protocol_tool_rejects_empty_query():
    tool = create_protocol_tools(StubRetriever())[0]

    try:
        tool.invoke({"query": "   "})
    except ValueError as error:
        assert "não pode ser vazia" in str(error)
    else:
        raise AssertionError("A consulta vazia deveria ser rejeitada")
