# ==============================================================================
# ARQUIVO: dashboard/pages/2_💸_Transacoes.py
# FUNÇÃO: Exibe a lista detalhada de transações do usuário.
# ==============================================================================
import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Transações", layout="wide")
API_URL = "http://127.0.0.1:8000"

# Verifica se o usuário está logado (agora checando pelo access_token)
if 'access_token' not in st.session_state:
    st.error("⚠️ Você precisa fazer o login para acessar esta página.")
    st.switch_page("login.py")
    st.stop()

st.title("💸 Minhas Transações")
st.markdown("Veja aqui o detalhe de todas as suas movimentações.")

# O cache agora depende do token, então se o usuário mudar, os dados são recarregados.
@st.cache_data
def carregar_transacoes(access_token):
    """Busca as transações do usuário autenticado na API FastAPI."""
    if not access_token: return []
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        # Chama o novo endpoint seguro
        response = requests.get(f"{API_URL}/transactions/me", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Se o token for inválido/expirado (erro 401), podemos deslogar o usuário
        if e.response and e.response.status_code == 401:
            st.error("Sua sessão expirou. Por favor, faça o login novamente.")
            # Limpa a sessão e redireciona (opcional, mas recomendado)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("login.py")
        else:
            st.error(f"Não foi possível buscar suas transações. Verifique sua conexão.")
        return None

if lista_transacoes is not None:
    if lista_transacoes:
        df = pd.DataFrame(lista_transacoes)
        # Converte a coluna de valor para numérico para garantir a formatação correta
        df['valor'] = pd.to_numeric(df['valor'])
        
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