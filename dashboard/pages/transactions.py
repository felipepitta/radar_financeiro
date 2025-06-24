# -----------------------------------------------------------------------------
# pages/2_💸_Transacoes.py - Visualização e Edição de Transações
# -----------------------------------------------------------------------------
# Esta página é responsável por buscar e exibir a lista de transações do
# usuário logado, permitindo interações como edição e seleção.
# -----------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import requests

# --- Configurações e Verificação de Login ---

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Transações", layout="wide")

# Bloco de segurança: Garante que apenas usuários logados acessem a página.
if 'user_email' not in st.session_state:
    st.error("Você precisa fazer o login para acessar esta página.")
    st.markdown("Por favor, retorne à página de **Login**.")
    st.stop() # Interrompe a execução do script

st.title("💸 Minhas Transações")
st.markdown("Veja aqui o detalhe de todas as suas movimentações. Você pode clicar em uma célula para editar seu conteúdo.")

# --- Função para Carregar Dados (com Cache) ---

# @st.cache_data é um "decorador" que otimiza a performance. Ele armazena o resultado
# da função em cache, evitando fazer chamadas repetidas à API a cada interação na página.
@st.cache_data
def carregar_transacoes(user_phone, access_token):
    """Busca as transações do usuário na API FastAPI."""
    try:
        # Futuramente, passaremos o token de acesso no cabeçalho para segurança
        # headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{API_URL}/users/{user_phone}/transactions") #, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        # Se for 404, não é um erro, apenas não há dados. Retorna uma lista vazia.
        if e.response.status_code == 404:
            return []
        else:
            # Para outros erros HTTP, mostra a mensagem.
            st.error(f"Erro ao buscar transações: {e}")
            return None
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar os dados: {e}")
        return None

# --- Lógica Principal de Exibição ---

telefone = st.session_state.get("telefone_usuario_normalizado") # Usaremos um telefone normalizado salvo na sessão
access_token = st.session_state.get("access_token")

# Futuramente, o telefone e o token virão da sessão após o login
# Por enquanto, vamos simular para fins de layout
if not telefone:
    telefone = "5511988831474" # Simulação temporária

lista_transacoes = carregar_transacoes(telefone, access_token)


# Se a chamada à API foi bem-sucedida
if lista_transacoes is not None:
    # Se a lista não estiver vazia, mostramos o editor de dados
    if lista_transacoes:
        df = pd.DataFrame(lista_transacoes)
        
        st.info("💡 Clique em uma célula para editar o Item ou a Categoria. As edições ainda não são salvas no banco.")

        # O Data Editor: o coração da nossa nova página.
        df_editado = st.data_editor(
            df,
            column_config={
                "created_at": st.column_config.DatetimeColumn("Data", format="DD/MM/YYYY HH:mm", disabled=True),
                "item": st.column_config.TextColumn("Item", required=True),
                "categoria": st.column_config.SelectboxColumn(
                    "Categoria",
                    options=['Receita', 'Alimentação', 'Transporte', 'Lazer', 'Moradia', 'Trabalho', 'Outros'],
                    required=True
                ),
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", disabled=True)
            },
            use_container_width=True, 
            hide_index=True,
            # 'num_rows="dynamic"' permitiria adicionar/deletar linhas, mas faremos isso de outra forma.
        )
        
        # Futuramente, aqui teremos um botão "Salvar Alterações" que pegará 'df_editado'
        # e enviará as mudanças para um novo endpoint na nossa API.

    else:
        st.success("✔️ Nenhuma transação encontrada. Seu extrato está limpo! Comece a enviar seus gastos pelo WhatsApp.")