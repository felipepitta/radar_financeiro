import streamlit as st
import pandas as pd
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Transações", layout="wide")

if 'user' not in st.session_state:
    st.error("Você precisa fazer o login para acessar esta página.")
    st.stop()

st.title("💸 Minhas Transações")
st.markdown("Veja aqui o detalhe de todas as suas movimentações.")

try:
    telefone_usuario = st.session_state.user.user_metadata.get("phone")
    if not telefone_usuario:
        st.warning("Seu usuário não tem um número de telefone cadastrado.")
        st.stop()
        
    response = requests.get(f"{API_URL}/users/{telefone_usuario}/transactions")
    response.raise_for_status()
    
    lista_transacoes = response.json()
    
    if lista_transacoes:
        df = pd.DataFrame(lista_transacoes)
        st.dataframe(
            df[['created_at', 'item', 'categoria', 'valor']],
            column_config={
                "created_at": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm"),
                "item": "Item", "categoria": "Categoria",
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
            },
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Nenhuma transação encontrada para este usuário.")
        
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        st.info("Nenhuma transação encontrada. Comece a enviar seus gastos pelo WhatsApp!")
    else:
        st.error(f"Erro ao buscar transações: {e}")
except Exception as e:
    st.error(f"Ocorreu um erro inesperado: {e}")