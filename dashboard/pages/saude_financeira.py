# ==============================================================================
# ARQUIVO: dashboard/pages/3_🩺_Saude_Financeira.py
# FUNÇÃO: Página placeholder para a análise detalhada da saúde financeira.
# ==============================================================================
import streamlit as st

st.set_page_config(page_title="Saúde Financeira", layout="wide")

if 'user_email' not in st.session_state:
    st.error("⚠️ Você precisa fazer o login para acessar esta página.")
    st.switch_page("login.py")
    st.stop()

st.title("🩺 Saúde Financeira")
st.markdown("---")
st.info("Em breve: Uma análise profunda dos seus hábitos financeiros, com gráficos interativos sobre seu patrimônio, dívidas e fluxo de caixa.")