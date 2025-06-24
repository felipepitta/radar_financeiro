# ==============================================================================
# ARQUIVO: dashboard/pages/2_💸_Transacoes.py
# FUNÇÃO: Exibe a lista detalhada de transações do usuário.
# ==============================================================================
import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Transações", layout="wide")
API_URL = "http://127.0.0.1:8000"

if 'user_email' not in st.session_state:
    st.error("⚠️ Você precisa fazer o login para acessar esta página.")
    st.switch_page("login.py")
    st.stop()

st.title("💸 Minhas Transações")
st.markdown("Veja aqui o detalhe de todas as suas movimentações.")

@st.cache_data
def carregar_transacoes(user_phone):
    """Busca as transações do usuário na API FastAPI."""
    if not user_phone: return []
    try:
        response = requests.get(f"{API_URL}/users/{user_phone}/transactions")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return []
        else:
            st.error(f"Erro ao buscar transações: {e}")
            return None
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {e}")
        return None

# Busca o telefone a partir das informações do usuário salvas na sessão
user_info = st.session_state.get('user_info', {})
telefone = user_info.get('user_metadata', {}).get('phone')

lista_transacoes = carregar_transacoes(telefone)

if lista_transacoes is not None:
    if lista_transacoes:
        df = pd.DataFrame(lista_transacoes)
        st.dataframe(
            df[['created_at', 'item', 'categoria', 'valor']],
            column_config={
                "created_at": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm"),
                "item": "Item",
                "categoria": "Categoria",
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
            },
            use_container_width=True, hide_index=True
        )
    else:
        st.success("✔️ Nenhuma transação encontrada. Comece a enviar seus gastos pelo WhatsApp!")