# streamlit_frontend.py
import streamlit as st
from chatbot import Chatbot
from agent.state import inicializar_estado_sessao

# --- 1. Configuração da Página ---
st.set_page_config(page_title="Assistente de Vendas IA", layout="wide")

# --- 2. Inicialização do Agente e do Estado ---
# @st.cache_resource
def carregar_chatbot():
    return Chatbot()

chatbot_agent = carregar_chatbot()

# A mágica acontece aqui: inicializamos o estado completo da sessão
inicializar_estado_sessao()

# --- 3. Painel Lateral (Sidebar) com Dados do Estado Real ---
with st.sidebar:
    st.header("Status do Lead (Debug)")

    # Agora os valores vêm DIRETAMENTE do st.session_state
    st.text_input("Nome", value=st.session_state.lead_slots["user_name"], disabled=True)
    st.text_input("E-mail", value=st.session_state.lead_slots["email"], disabled=True)
    st.text_input("Estágio do Funil", value=st.session_state.conversation_stage, disabled=True)

    st.divider()

    st.header("Análise da Conversa (Debug)")
    st.text_input("Intenção Detectada", value=st.session_state.debug_info["intencao"], disabled=True)
    st.text_input("Score RAG", value=st.session_state.debug_info["score_rag"], disabled=True)

    st.divider()
    if st.button("Encaminhar ao Comercial (Ação Manual)"):
        st.success("Handoff para a equipe comercial disparado!")
        st.session_state.conversation_stage = "Handoff"
        st.rerun() # Corrigido aqui também


# --- 4. Área Principal do Chat ---
st.title("🤖 Assistente de Vendas IA")
st.caption("Esta é a visão de console para desenvolvimento e debug do agente.")
st.divider()

# Exibe as mensagens do histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Captura a nova mensagem do usuário e aplica a lógica de atualização
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            response = chatbot_agent.executar(
                mensagem_usuario=prompt,
                estado_sessao=st.session_state
            )
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

    # MUDANÇA CORRIGIDA: Usamos a função oficial st.rerun()
    st.rerun()