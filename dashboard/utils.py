# ==============================================================================
# ARQUIVO: dashboard/utils.py
# FUNÇÃO: Armazena funções utilitárias compartilhadas entre as páginas do dashboard.
# AUTOR: Gem Radar
# ==============================================================================
import pandas as pd
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

@st.cache_data(show_spinner="Buscando transações...")
def carregar_transacoes(access_token: str) -> pd.DataFrame:
    """
    Busca as transações do usuário na API, trata erros e retorna um DataFrame.
    Esta função está centralizada para ser usada por todo o app.
    """
    if not access_token:
        return pd.DataFrame()
        
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{API_URL}/transactions/me", headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        # Conversões e limpezas centrais
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce').dt.date
        df['valor'] = pd.to_numeric(df['valor'])

        # SIMULAÇÃO DA COLUNA 'tipo' (Mantenha como no home.py original)
        if 'tipo' not in df.columns:
            df['tipo'] = 'Saída'
        
        return df

    except requests.exceptions.RequestException as e:
        if e.response and e.response.status_code == 401:
            st.error("Sua sessão expirou. Por favor, faça o login novamente.")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("login.py")
        else:
            st.error("Não foi possível buscar suas transações. Verifique a conexão com a API.")
        return None