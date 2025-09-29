# agent/state.py
import streamlit as st
from datetime import datetime

# Define os "slots" que queremos preencher sobre o lead
LEAD_SLOTS_INICIAIS = {
    "user_name": "Ainda não coletado",
    "email": "Ainda não coletado",
    "pilar_interesse": "N/A",
    "necessidades": "N/A",
    "dor": "N/A",
    "objetivo": "N/A",
    "prazo": "N/A",
}

# Define os estágios possíveis da conversa
STAGES = ["Inicial", "Qualificacao", "Agendamento", "Handoff", "Finalizado"]

# Define as informações de debug que queremos ver
DEBUG_INFO_INICIAIS = {
    "intencao": "N/A",
    "score_rag": "0.00",
}

def inicializar_estado_sessao():
    """
    Função para configurar o st.session_state com todas as nossas
    estruturas de memória na primeira vez que o app é executado.
    """
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Olá! Sou o assistente de vendas. Como posso ajudar?"}]

    if "lead_slots" not in st.session_state:
        st.session_state.lead_slots = LEAD_SLOTS_INICIAIS.copy()

    if "conversation_stage" not in st.session_state:
        st.session_state.conversation_stage = STAGES[0]

    if "debug_info" not in st.session_state:
        st.session_state.debug_info = DEBUG_INFO_INICIAIS.copy()

    if "last_user_message_at" not in st.session_state:
        st.session_state.last_user_message_at = None