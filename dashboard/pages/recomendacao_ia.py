# ==============================================================================
# ARQUIVO: dashboard/pages/4_🤖_Recomendacao_IA.py
# FUNÇÃO: Página placeholder para interagir com a IA para obter recomendações.
# ==============================================================================
import streamlit as st

st.set_page_config(page_title="Recomendações da IA", layout="wide")

if 'user_email' not in st.session_state:
    st.error("⚠️ Você precisa fazer o login para acessar esta página.")
    st.switch_page("login.py")
    st.stop()

st.title("🤖 Converse com seu Assistente IA")
st.markdown("---")
st.info("Em breve: Uma interface de chat para você fazer perguntas como 'Onde posso economizar?' ou 'Faça um plano para eu quitar meu cartão de crédito'.")
