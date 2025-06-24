# -----------------------------------------------------------------------------
# 1_🏠_Home.py - Página Principal do Dashboard
# -----------------------------------------------------------------------------
# Este arquivo representa a primeira página que o usuário vê após o login.
# O nome do arquivo com "1_🏠_" é um truque do Streamlit para ordenar e
# adicionar um ícone ao item no menu de navegação lateral.
# -----------------------------------------------------------------------------

# 1. Imports
import streamlit as st

# 2. Configuração da Página
st.set_page_config(page_title="Home", layout="wide")

# 3. Guarda de Autenticação
# Esta é a verificação de segurança mais importante em qualquer página restrita.
# Ele checa na "memória da sessão" se a informação do usuário logado existe.
# Usamos 'user_email' para manter a consistência com o que salvamos no login.py.
if 'user_email' not in st.session_state:
    st.error("⚠️ Você precisa fazer o login para acessar esta página.")
    # st.stop() interrompe a execução do restante do script, garantindo
    # que nenhum dado sensível seja exibido.
    st.stop()

# 4. Conteúdo da Página
# Se o código chegou até aqui, significa que o usuário está autenticado.

# Exibe o status de login e o botão de logout na barra lateral para fácil acesso.
with st.sidebar:
    st.success(f"Logado como:\n{st.session_state.user_email}")
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- Título e Layout Principal ---
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

# Por enquanto, esta página serve como um "placeholder" para nossas futuras funcionalidades.
st.info("Em breve, esta página estará repleta de gráficos e insights! ✨")