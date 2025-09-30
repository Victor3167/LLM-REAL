# chatbot.py
import streamlit as st
from llama_index.llms.ollama import Ollama
from agent.prompts import PROMPT_EXTRACAO_NOME, PROMPT_EXTRACAO_EMAIL, PROMPT_PEDIDO_EMAIL, PROMPT_SINTESE_RAG
from tools.rag import buscar_informacao
import re

class Chatbot:
    """
    Versão 3.3: Adicionado tratamento para remover aspas da resposta final.
    """
    def __init__(self):
        self.llm = Ollama(model="qwen2:7b", request_timeout=120.0)
        self.contato_whatsapp = "https://wa.me/554333719562" # Centralizamos o link de contato

    def _limpar_extracao(self, texto_bruto: str) -> str:
        """Limpa o texto extraído, removendo prefixos como 'Nome:' ou 'E-mail:'."""
        if ':' in texto_bruto:
            return texto_bruto.split(':')[-1].strip()
        return texto_bruto.strip()

    def _extrair_nome_usuario(self, mensagem_usuario: str, estado_sessao: st.delta_generator.DeltaGenerator):
        """Extrai o nome do usuário da mensagem se ainda não foi coletado."""
        if estado_sessao.lead_slots["user_name"] == "Ainda não coletado":
            prompt = PROMPT_EXTRACAO_NOME.format(mensagem_usuario=mensagem_usuario)
            nome_bruto = self.llm.complete(prompt).text
            nome_limpo = self._limpar_extracao(nome_bruto)
            if "N/A" not in nome_limpo and len(nome_limpo) > 2:
                estado_sessao.lead_slots["user_name"] = nome_limpo

    def _extrair_e_validar_email(self, mensagem_usuario: str, estado_sessao: st.delta_generator.DeltaGenerator) -> tuple[bool, str]:
        """Extrai e valida um e-mail da mensagem do usuário."""
        prompt = PROMPT_EXTRACAO_EMAIL.format(mensagem_usuario=mensagem_usuario)
        email_bruto = self.llm.complete(prompt).text
        email_limpo = self._limpar_extracao(email_bruto)
        if "N/A" not in email_limpo and re.match(r"[^@]+@[^@]+\.[^@]+", email_limpo):
            estado_sessao.lead_slots["email"] = email_limpo
            estado_sessao.conversation_stage = "Qualificacao"
            return (True, email_limpo)
        return (False, "")

    def executar(self, mensagem_usuario: str, estado_sessao: st.delta_generator.DeltaGenerator) -> str:
        """
        Executa a lógica principal do chatbot, priorizando a resposta antes da qualificação.
        """
        # 1. Tenta extrair dados do usuário a cada mensagem
        self._extrair_nome_usuario(mensagem_usuario, estado_sessao)
        sucesso_email, email_coletado = self._extrair_e_validar_email(mensagem_usuario, estado_sessao)

        if sucesso_email:
            nome = estado_sessao.lead_slots["user_name"]
            if nome != "Ainda não coletado":
                return f"Ótimo, {nome}! E-mail {email_coletado} registrado. Agora, me diga, qual seu principal desafio de marketing hoje?"
            else:
                return f"E-mail {email_coletado} registrado! Agora, para continuarmos, qual seu principal desafio de marketing hoje?"

        # 2. Detecta a intenção de falar com um especialista ANTES de qualquer outra coisa
        palavras_chave_contato = ['especialista', 'contato', 'falar', 'conectar', 'humano']
        mensagem_lower = mensagem_usuario.lower()
        if any(palavra in mensagem_lower for palavra in palavras_chave_contato):
            return f"Claro! Para falar com um de nossos especialistas e obter um diagnóstico gratuito, entre em contato diretamente pelo WhatsApp: {self.contato_whatsapp}"

        # 3. Se não for a intenção de contato, tenta responder usando RAG
        contexto_rag, score_rag = buscar_informacao(mensagem_usuario)
        estado_sessao.debug_info["score_rag"] = f"{score_rag:.2f}"

        if score_rag > 0.5:
            prompt_sintese = PROMPT_SINTESE_RAG.format(
                contexto_rag=contexto_rag,
                pergunta_cliente=mensagem_usuario
            )
            resposta = self.llm.complete(prompt_sintese).text
            # >>>>> AQUI ESTÁ A CORREÇÃO <<<<<
            # Remove aspas do início e do fim da string, se existirem.
            return resposta.strip('"')

        # 4. Se o RAG falhou, verifica se precisa pedir o e-mail
        if estado_sessao.lead_slots["email"] == "Ainda não coletado":
            return self.llm.complete(PROMPT_PEDIDO_EMAIL).text
        
        # 5. Se o RAG falhou e o e-mail JÁ foi coletado, usa a resposta de handoff
        return "Essa é uma ótima pergunta. Não encontrei informações específicas sobre isso em minha base, mas posso conectar você com um de nossos especialistas para uma análise mais aprofundada. O que acha?"