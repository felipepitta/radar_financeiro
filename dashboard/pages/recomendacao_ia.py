# ==============================================================================
# ARQUIVO: dashboard/pages/4_🤖_Recomendacao_IA.py
# FUNÇÃO: Interface de chat para obter recomendações da IA.
# AUTOR: Gem Radar
# ==============================================================================
import streamlit as st
import requests
import pandas as pd

# URL do nosso futuro endpoint no backend FastAPI
# (usaremos um placeholder por enquanto)
API_URL = "http://127.0.0.1:8000" # Lembre-se de usar sua URL do ngrok durante o teste

st.set_page_config(page_title="Recomendações da IA", layout="wide")

# --- Funções de Apoio ---
def get_ai_recommendation(question_text: str, token: str):
    """Função para chamar nosso backend e obter a resposta da IA."""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"question": question_text}
    
    try:
        response = requests.post(f"{API_URL}/ai/ask", headers=headers, json=payload)
        response.raise_for_status() # Lança um erro para respostas 4xx ou 5xx
        return response.json().get("answer", "Não recebi uma resposta válida da IA.")
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão ao tentar falar com a IA: {e}")
        return "Desculpe, não consegui me conectar ao nosso servidor de IA."


# --- Verificação de Login ---
if 'access_token' not in st.session_state or not st.session_state['access_token']:
    st.error("⚠️ Você precisa fazer o login para acessar esta página.")
    st.switch_page("login.py")
    st.stop()

token = st.session_state.get('access_token')

# --- Interface da Página ---
st.title("🤖 Converse com seu Assistente IA")
st.markdown("Selecione uma das perguntas abaixo para que nossa IA analise seu histórico financeiro e te dê insights valiosos.")

# Inicializa o histórico do chat no session_state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Olá! Sou seu assistente financeiro. Como posso ajudar hoje?"}]

# Mostra as mensagens do histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Perguntas pré-definidas
predefined_questions = [
    "Onde gastei mais dinheiro no último mês?",
    "Sugira 3 categorias onde posso tentar economizar no próximo mês.",
    "Meus gastos com 'Alimentação' este mês foram maiores ou menores que a média dos últimos 3 meses?",
    "Faça um resumo narrativo da minha saúde financeira do mês passado (receitas, despesas, saldo).",
    "Com base nos meus hábitos, crie um plano simples de 3 passos para melhorar minhas finanças."
]

# Exibe as perguntas como botões em colunas
st.markdown("---")
st.subheader("Sugestões de Análise:")
cols = st.columns(2)
for i, question in enumerate(predefined_questions):
    if cols[i % 2].button(question, use_container_width=True, key=f"question_{i}"):
        # 1. Adiciona a pergunta do usuário ao chat
        st.session_state.messages.append({"role": "user", "content": question})
        
        # 2. Mostra a pergunta imediatamente na tela
        with st.chat_message("user"):
            st.markdown(question)
        
        # 3. Chama a IA (nosso backend) e mostra a resposta
        with st.chat_message("assistant"):
            with st.spinner("Analisando seus dados e consultando a IA..."):
                response_text = get_ai_recommendation(question, token)
                st.markdown(response_text)
        
        # 4. Adiciona a resposta da IA ao histórico
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        # O st.rerun() abaixo é opcional, mas pode ajudar a manter o estado limpo
        # st.rerun()