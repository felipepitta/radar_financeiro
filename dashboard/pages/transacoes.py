# ==============================================================================
# ARQUIVO: dashboard/pages/2_💸_Transacoes.py
# FUNÇÃO: Apresenta um dashboard financeiro para visualização, filtragem e
#         edição de transações individuais.
# AUTOR: Gem Radar
# ==============================================================================

# --- 1. SETUP INICIAL ---
# Importação das bibliotecas necessárias
import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta, date

# Constantes e configurações da página
st.set_page_config(page_title="Histórico de Transações", layout="wide", initial_sidebar_state="collapsed")
API_URL = "http://127.0.0.1:8000"

# --- 2. FUNÇÕES DE APOIO ---

def aplicar_estilos_customizados():
    """
    Injeta um bloco de CSS para customizar a aparência da tabela de dados.
    """
    st.markdown("""
        <style>
            /* Altera o container principal do cabeçalho da tabela */
            [data-testid="stDataFrame"] .col-header {
                background-color: #0d47a1; /* Um tom de azul escuro e elegante */
                color: white;
                font-weight: bold;
                text-align: center;
            }
            
            /* Centraliza o texto dentro do cabeçalho */
            [data-testid="stDataFrame"] .col-header-name {
                text-align: center;
                justify-content: center;
                width: 100%;
            }

            /* Altera as células de dados da tabela */
            [data-testid="stDataFrame"] .data-grid-cell {
                font-size: 16px; /* Aumenta um pouco o tamanho da fonte */
                text-align: center !important; /* Força o alinhamento central */
                justify-content: center !important; /* Necessário para alguns tipos de célula */
            }
        </style>
    """, unsafe_allow_html=True)

@st.cache_data(show_spinner="Buscando transações...")
def carregar_transacoes(access_token: str) -> pd.DataFrame:
    """
    Busca as transações do usuário na API, trata erros e retorna um DataFrame.
    A função é cacheada para otimizar o desempenho.
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
        # Converte as colunas para os tipos corretos, garantindo consistência
        # O argumento 'coerce' transforma erros de conversão em NaT (Not a Time)
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce').dt.date
        df['valor'] = pd.to_numeric(df['valor'])
        return df

    except requests.exceptions.RequestException as e:
        if e.response and e.response.status_code == 401:
            st.error("Sua sessão expirou. Por favor, faça o login novamente.")
            # Limpa a sessão para um logout seguro e redireciona
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("login.py")
        else:
            st.error("Não foi possível buscar suas transações. Verifique a conexão com a API.")
        return None

# --- 3. FLUXO PRINCIPAL DA PÁGINA ---

# Passo 3.0: Aplica os estilos customizados no início da renderização
aplicar_estilos_customizados()

# Passo 3.1: Segurança - Verificar se o usuário está logado
if 'access_token' not in st.session_state or not st.session_state['access_token']:
    st.error("⚠️ Você precisa fazer o login para acessar esta página.")
    st.switch_page("login.py")
    st.stop()

# Passo 3.2: Carregar os dados iniciais
token = st.session_state.get('access_token')
df_original = carregar_transacoes(token)

if df_original is None:
    st.error("Falha ao carregar os dados. A aplicação será interrompida.")
    st.stop()

# Passo 3.3: Renderizar o Título do Dashboard
st.title("📊 Dashboard de Transações")
st.markdown("Analise suas movimentações de forma rápida e intuitiva.")

# Passo 3.4: Renderizar os Filtros de Data
with st.expander("📅 Filtros de Período", expanded=True):
    # ==================== INÍCIO DA LÓGICA CORRIGIDA ====================
    def obter_data_minima_segura(df: pd.DataFrame) -> date:
        """Função auxiliar para obter a data mínima de forma segura."""
        if not df.empty and 'created_at' in df.columns:
            # Remove quaisquer datas nulas (NaT) antes de calcular o mínimo
            datas_validas = df['created_at'].dropna()
            if not datas_validas.empty:
                return datas_validas.min()
        return date.today()

    # Inicializa as datas no estado da sessão se não existirem
    if 'start_date' not in st.session_state:
        st.session_state['start_date'] = obter_data_minima_segura(df_original)
    if 'end_date' not in st.session_state:
        st.session_state['end_date'] = date.today()
    # ===================== FIM DA LÓGICA CORRIGIDA ======================

    # Botões de filtro rápido
    botoes_col1, botoes_col2, botoes_col3, botoes_col4 = st.columns(4)
    if botoes_col1.button("Este Mês", use_container_width=True):
        st.session_state['start_date'] = date.today().replace(day=1)
        st.session_state['end_date'] = date.today()
        st.rerun()

    if botoes_col2.button("Últimos 30 dias", use_container_width=True):
        st.session_state['start_date'] = date.today() - timedelta(days=30)
        st.session_state['end_date'] = date.today()
        st.rerun()
        
    if botoes_col4.button("Limpar Filtros", use_container_width=True, type="primary"):
        st.session_state['start_date'] = obter_data_minima_segura(df_original)
        st.session_state['end_date'] = date.today()
        st.rerun()

    # Seletores de data
    datas_col1, datas_col2 = st.columns(2)
    start_date = datas_col1.date_input("Data Inicial", value=st.session_state['start_date'])
    end_date = datas_col2.date_input("Data Final", value=st.session_state['end_date'])

# Passo 3.5: Aplicar o filtro e criar o DataFrame filtrado
# Garantir que a comparação não falhe se o dataframe estiver vazio
if not df_original.empty:
    df_filtrado = df_original[
        (df_original['created_at'] >= start_date) & 
        (df_original['created_at'] <= end_date)
    ]
else:
    df_filtrado = pd.DataFrame()


st.divider()

# Passo 3.6: Renderizar os KPIs (Indicadores Chave de Performance)
st.subheader("Resumo do Período")
if not df_filtrado.empty:
    # Cálculos dos indicadores
    total_gasto = df_filtrado['valor'].sum()
    num_transacoes = len(df_filtrado)
    media_por_transacao = total_gasto / num_transacoes if num_transacoes > 0 else 0
    categoria_mais_comum = df_filtrado['categoria'].mode()[0] if not df_filtrado['categoria'].empty and not df_filtrado['categoria'].isnull().all() else "N/A"

    # Exibição dos KPIs em colunas
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Gasto 💸", f"R$ {total_gasto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    kpi2.metric("Nº de Transações #️⃣", num_transacoes)
    kpi3.metric("Valor Médio 🏧", f"R$ {media_por_transacao:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    kpi4.metric("Principal Categoria 🏷️", categoria_mais_comum.title())
else:
    st.info("Não há dados para exibir os indicadores no período selecionado.")

st.divider()

# Passo 3.7: Renderizar a Tabela de Detalhes e a Lógica de Edição
st.subheader("Detalhes das Transações")
if df_filtrado.empty:
    st.success("✔️ Nenhuma transação encontrada para o período selecionado.")
else:
    # Renomear colunas para exibição amigável antes do data_editor
    df_para_exibir = df_filtrado.copy()
    df_para_exibir.insert(0, "Selecionar", False)
    
    # Exibe a tabela interativa
    df_editado = st.data_editor(
        df_para_exibir,
        column_config={
            "id": None, # Oculta a coluna de ID
            "owner_id": None, # Oculta a coluna de owner_id
            "Selecionar": st.column_config.CheckboxColumn(required=True),
            "created_at": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "item": "Item", 
            "categoria": "Categoria",
            "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
        },
        use_container_width=True, hide_index=True, key="transaction_editor", 
        disabled=["created_at", "item", "categoria", "valor"]
    )

    # Lógica para identificar a linha selecionada e exibir o formulário de edição
    transacoes_selecionadas = df_editado[df_editado['Selecionar']]
    if len(transacoes_selecionadas) == 1:
        with st.form("form_edicao_unica"):
            transacao_para_editar = transacoes_selecionadas.iloc[0]
            st.write(f"**Editando item:** {transacao_para_editar['item']}")

            # Layout do formulário em grade
            row1_col1, row1_col2 = st.columns(2)
            novo_item = row1_col1.text_input("Nome do Item", value=transacao_para_editar['item'])
            nova_categoria = row1_col1.text_input("Categoria", value=transacao_para_editar['categoria'])
            novo_valor = row1_col2.number_input("Valor (R$)", value=float(transacao_para_editar['valor']), format="%.2f", step=0.01)
            nova_data = row1_col2.date_input("Data", value=transacao_para_editar['created_at'])

            # Botão de submissão e lógica de chamada à API
            if st.form_submit_button("Salvar Alterações", use_container_width=True):
                payload = {
                    "item": novo_item, "valor": novo_valor,
                    "categoria": nova_categoria, "created_at": nova_data.isoformat()
                }
                headers = {"Authorization": f"Bearer {token}"}
                try:
                    response = requests.put(f"{API_URL}/transactions/{int(transacao_para_editar['id'])}", json=payload, headers=headers)
                    response.raise_for_status()
                    st.success("Transação alterada com sucesso!")
                    time.sleep(1)
                    # Limpa o cache para forçar o recarregamento dos dados da API
                    st.cache_data.clear()
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    st.error(f"Falha ao salvar: {e.response.json() if e.response else e}")
    elif len(transacoes_selecionadas) > 1:
        st.error("⚠️ **Apenas uma transação pode ser editada por vez.**")

# Passo 3.8: Renderizar o Rodapé
st.divider()
st.markdown("© 2025 Radar Financeiro. Todos os direitos reservados.")