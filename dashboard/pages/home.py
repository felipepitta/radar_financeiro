import streamlit as st

st.set_page_config(page_title="Home", layout="wide")

# Verifica se o usuário está logado, senão, o expulsa para a página de login
if 'user' not in st.session_state:
    st.error("Você precisa fazer o login para acessar esta página.")
    st.stop()

st.sidebar.success(f"Logado como: {st.session_state.user.email}")
st.title("🏠 Página Principal (Home)")
st.markdown("---")

st.header("Aqui teremos as informações macro!")
st.markdown("""
Neste espaço, vamos construir os visuais principais da saúde financeira do usuário:
- **Score de Saúde Financeira:** Um número de 0 a 1000.
- **Gráfico de Receita vs. Despesa:** Um resumo visual do mês.
- **Recomendações da IA:** Insights e dicas rápidas geradas pela nossa IA.
- **Alertas Importantes:** Como "Cuidado, seus gastos com Lazer aumentaram 30% este mês!".
""")
# Por enquanto, é apenas um placeholder.