"""Interface de demonstração do assistente médico acadêmico."""

from __future__ import annotations

import streamlit as st

from app.database.seed import DEFAULT_DATABASE, seed_database
from app.graph.workflow import build_assistant_graph
from app.ui.presentation import build_result_view


PATIENT_OPTIONS = {
    "PAC-001": "Rotina — acompanhamento estável",
    "PAC-002": "Revisão clínica — medidas elevadas e exames pendentes",
    "PAC-003": "Revisão clínica — exames pendentes",
    "PAC-004": "Alerta — sintomas de emergência",
    "PAC-005": "Cadastro com dados ausentes",
}


st.set_page_config(
    page_title="Assistente Médico Acadêmico",
    page_icon="🩺",
    layout="wide",
)


@st.cache_resource(show_spinner="Carregando banco, protocolos e modelos...")
def get_graph():
    if not DEFAULT_DATABASE.exists():
        seed_database(DEFAULT_DATABASE)
    return build_assistant_graph()


def show_priority(view: dict) -> None:
    message = f"Prioridade definida pelo fluxo: **{view['priority_label']}**"
    if view["priority"] == "revisao_imediata":
        st.error(message, icon="🚨")
    elif view["blocked"] or view["priority"] == "dados_insuficientes":
        st.warning(message, icon="⚠️")
    elif view["priority"] == "revisao_clinica":
        st.warning(message, icon="🩺")
    else:
        st.success(message, icon="✅")


st.title("🩺 Assistente Médico Acadêmico")
st.caption("Demonstração de fine-tuning, RAG, LangChain, LangGraph e guardrails")
st.warning(
    "Protótipo exclusivamente acadêmico com dados sintéticos. Não realiza "
    "diagnóstico ou prescrição e não substitui avaliação profissional.",
    icon="⚠️",
)

with st.form("assistant_request"):
    patient_id = st.selectbox(
        "Paciente sintético",
        options=list(PATIENT_OPTIONS),
        format_func=lambda item: f"{item} — {PATIENT_OPTIONS[item]}",
    )
    question = st.text_area(
        "Pergunta",
        value="Quais exames estão pendentes?",
        height=100,
        help="Experimente também pedidos proibidos ou o cenário PAC-004.",
    )
    submitted = st.form_submit_button(
        "Analisar com o assistente", type="primary", use_container_width=True
    )

if submitted:
    try:
        with st.spinner("Executando o fluxo seguro..."):
            result = get_graph().invoke(
                {"patient_id": patient_id, "question": question}
            )
        st.session_state["last_result"] = result
    except Exception as error:
        st.error(f"Não foi possível executar o fluxo: {type(error).__name__}: {error}")

if result := st.session_state.get("last_result"):
    view = build_result_view(result)
    st.divider()
    show_priority(view)

    priority_column, model_column, fallback_column = st.columns(3)
    priority_column.metric("Prioridade", view["priority_label"])
    model_column.metric("Modelo", view["model_name"])
    fallback_column.metric("Fallback de segurança", view["fallback_label"])

    st.subheader("Resposta")
    st.write(view["answer"])
    if view["fallback"]:
        st.info(
            "A resposta da LLM foi substituída por conteúdo determinístico. "
            f"Motivo técnico: `{view['fallback_reason']}`."
        )
    if view["human_validation_required"]:
        st.caption("Validação por profissional habilitado: obrigatória.")

    with st.expander("Fontes e rastreabilidade"):
        st.markdown("**Fontes consultadas**")
        for source in view["sources"]:
            st.code(source, language=None)
        st.markdown("**Nós executados no LangGraph**")
        st.write(" → ".join(view["executed_nodes"]))
        st.markdown("**Auditoria**")
        st.code(f"run_id: {view['run_id']}\nhorário UTC: {view['audited_at']}")

