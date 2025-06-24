# ==============================================================================
# ARQUIVO: dashboard/pages/1_🏠_Home.py
# FUNÇÃO: A página principal que o usuário vê após o login.
# ==============================================================================
import streamlit as st

st.set_page_config(page_title="Home", layout="wide")

# Guarda de Autenticação
if 'user_email' not in st.session_state:
    st.error("⚠️ Você precisa fazer o login para acessar esta página.")
    st.switch_page("login.py")
    st.stop()

with st.sidebar:
    st.success(f"Logado como:\n{st.session_state.user_email}")
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("login.py")

st.title("🏠 Página Principal (Home)")
st.markdown("---")
st.header("Visão Geral da sua Saúde Financeira")

# --- PLACEHOLDERS PARA FUTUROS COMPONENTES ---
col1, col2 = st.columns(2)
with col1:
    st.metric("Score de Saúde Financeira", "750", "+50 este mês")
    st.write("Em breve, um gráfico de Receita vs. Despesa aqui.")

with col2:
    st.subheader("💡 Recomendações da IA")
    st.info("Parabéns! Seus gastos com 'Alimentação' diminuíram 15% em relação ao mês passado.")
    st.warning("Atenção: Você não registrou nenhuma 'Receita' este mês.")