# dashboard/dashboard.py (este é o código correto e completo)

import streamlit as st
import pandas as pd
import requests # Biblioteca para fazer requisições HTTP
from decimal import Decimal

# URL base da sua API FastAPI (que deve estar rodando em outro terminal)
API_URL = "http://127.0.0.1:8000"

st.set_page_config(layout="wide")
st.title("Radar Financeiro - Painel de Controle 📈")
st.markdown("---")

# --- Identificação do Usuário na Barra Lateral ---
st.sidebar.header("👤 Identificação")
telefone_usuario = st.sidebar.text_input("Digite seu número de telefone (ex: 5511999999999)", key="telefone")

if not telefone_usuario:
    st.info("👈 Por favor, identifique-se na barra lateral para começar.")
    st.stop() # Para a execução do script se não houver telefone

st.sidebar.success(f"Logado como: {telefone_usuario}")

# --- Layout em duas colunas ---
col1, col2 = st.columns(2)

# Coluna 1: Formulário para adicionar transação
with col1:
    st.header("Adicionar Nova Transação")
    with st.form("nova_transacao_form", clear_on_submit=True):
        valor_input = st.number_input("Valor (R$)", min_value=0.01, format="%.2f", step=0.01)
        descricao = st.text_input("Descrição", placeholder="Ex: Almoço no restaurante")
        tipo = st.radio("Tipo", ["gasto", "receita"], horizontal=True)
        
        submitted = st.form_submit_button("✔️ Adicionar")

        if submitted:
            
            if submitted:
                # ---> ADICIONE ESTA VERIFICAÇÃO <---
                if not descricao.strip():
                    st.error("O campo 'Descrição' não pode ser vazio.")
                    # st.stop() para a execução aqui se a descrição for vazia
                    st.stop() 
            
            # Monta a mensagem do comando, como se viesse do chatbot
            mensagem_comando = f"{tipo}: {valor_input} {descricao}"
            
            payload = { "telefone": telefone_usuario, "mensagem": mensagem_comando }
            
            try:
                # Faz a chamada POST para a sua API!
                response = requests.post(f"{API_URL}/webhook", json=payload)
                response.raise_for_status() # Lança um erro se a resposta for 4xx ou 5xx
                
                resposta_api = response.json()
                st.success(resposta_api.get("resposta", "Comando enviado com sucesso!"))
            except requests.exceptions.RequestException as e:
                st.error(f"Erro ao conectar com a API: {e}")

# Coluna 2: Tabela de transações existentes
with col2:
    st.header("Últimas Transações")
    
    # Adiciona um botão para forçar a atualização da tabela
    if st.button('Recarregar Transações'):
        pass # A simples existência do botão já faz o rerun

    try:
        # Faz a chamada GET para o novo endpoint da sua API
        response = requests.get(f"{API_URL}/users/{telefone_usuario}/events")
        response.raise_for_status()
        
        lista_transacoes = response.json()
        
        if lista_transacoes:
            df = pd.DataFrame(lista_transacoes)
            df['valor'] = pd.to_numeric(df['valor'])
            
            st.dataframe(
                df[['criado_em', 'tipo', 'descricao', 'valor']],
                column_config={
                    "criado_em": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm"),
                    "tipo": "Tipo", "descricao": "Descrição",
                    "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
                },
                use_container_width=True, hide_index=True
            )
        else:
            st.info("Nenhuma transação encontrada para este usuário.")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Não foi possível buscar as transações: {e}")