# chatbot.py
import streamlit as st
from llama_index.llms.ollama import Ollama
from agent.prompts import PROMPT_EXTRACAO_NOME, PROMPT_EXTRACAO_EMAIL, PROMPT_PEDIDO_EMAIL, PROMPT_SINTESE_RAG
from tools.rag import buscar_informacao
import re

class Chatbot:
    """
    Versão 3.1: Com guardrail de RAG baseado em score para evitar alucinação.
    """
    def __init__(self):
        self.llm = Ollama(model="qwen2:7b", request_timeout=120.0)

    # ... (as funções _limpar_extracao, _extrair_nome_usuario, _extrair_e_validar_email continuam iguais) ...
    def _limpar_extracao(self, texto_bruto: str) -> str:
        if ':' in texto_bruto:
            return texto_bruto.split(':')[-1].strip()
        return texto_bruto.strip()

    def _extrair_nome_usuario(self, mensagem_usuario: str, estado_sessao: st.delta_generator.DeltaGenerator):
        if estado_sessao.lead_slots["user_name"] == "Ainda não coletado":
            prompt = PROMPT_EXTRACAO_NOME.format(mensagem_usuario=mensagem_usuario)
            nome_bruto = self.llm.complete(prompt).text
            nome_limpo = self._limpar_extracao(nome_bruto)
            if "N/A" not in nome_limpo and len(nome_limpo) > 2:
                estado_sessao.lead_slots["user_name"] = nome_limpo

    def _extrair_e_validar_email(self, mensagem_usuario: str, estado_sessao: st.delta_generator.DeltaGenerator) -> tuple[bool, str]:
        prompt = PROMPT_EXTRACAO_EMAIL.format(mensagem_usuario=mensagem_usuario)
        email_bruto = self.llm.complete(prompt).text
        email_limpo = self._limpar_extracao(email_bruto)
        if "N/A" not in email_limpo and re.match(r"[^@]+@[^@]+\.[^@]+", email_limpo):
            estado_sessao.lead_slots["email"] = email_limpo
            estado_sessao.conversation_stage = "Qualificacao"
            return (True, email_limpo)
        return (False, "")

    def executar(self, mensagem_usuario: str, estado_sessao: st.delta_generator.DeltaGenerator) -> str:
        self._extrair_nome_usuario(mensagem_usuario, estado_sessao)
        sucesso_email, email_coletado = self._extrair_e_validar_email(mensagem_usuario, estado_sessao)

        if sucesso_email:
            nome = estado_sessao.lead_slots["user_name"]
            if nome != "Ainda não coletado":
                return f"Ótimo, {nome}! E-mail {email_coletado} registrado. Agora, me diga, qual seu principal desafio de marketing hoje?"
            else:
                return f"E-mail {email_coletado} registrado! Agora, para continuarmos, qual seu principal desafio de marketing hoje?"

        if estado_sessao.lead_slots["email"] == "Ainda não coletado":
            return self.llm.complete(PROMPT_PEDIDO_EMAIL).text

        # --- LÓGICA DE QUALIFICAÇÃO COM GUARDRAIL ---
        contexto_rag, score_rag = buscar_informacao(mensagem_usuario)
        estado_sessao.debug_info["score_rag"] = f"{score_rag:.2f}" # Atualiza o score na UI

        # A VERIFICAÇÃO CRÍTICA ACONTECE AQUI:
        if score_rag > 0.7:
            # Se a confiança é alta, usamos o RAG para responder
            prompt_sintese = PROMPT_SINTESE_RAG.format(
                contexto_rag=contexto_rag,
                pergunta_cliente=mensagem_usuario
            )
            return self.llm.complete(prompt_sintese).text
        else:
            # Se a confiança é baixa, usamos uma resposta segura de handoff
            return "Essa é uma ótima pergunta. Não encontrei informações específicas sobre isso em minha base, mas posso conectar você com um de nossos especialistas para uma análise mais aprofundada. O que acha?"