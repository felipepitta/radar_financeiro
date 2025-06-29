# ==============================================================================
# ARQUIVO: dashboard/pages/1_🏠_Home.py
# FUNÇÃO: Apresenta o dashboard principal (página inicial) com um resumo
#         da saúde financeira do usuário.
# AUTOR: Gem Radar
# ==============================================================================

# --- 1. SETUP INICIAL ---
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

# Importa a função centralizada do nosso novo arquivo de utilitários
from utils import carregar_transacoes

# Configurações da página
st.set_page_config(page_title="Dashboard Principal", layout="wide")


# --- 2. FUNÇÕES DE APOIO E GERAÇÃO DE GRÁFICOS ---
def criar_grafico_velocimetro(score: int) -> go.Figure:
    """Cria um gráfico de velocímetro (gauge) com Plotly."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': "Score de Saúde Financeira", 'font': {'size': 24}},
        gauge={
            'axis': {'range': [0, 1000], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#0d47a1"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 250], 'color': '#d32f2f'},
                {'range': [250, 500], 'color': '#ffc107'},
                {'range': [500, 750], 'color': '#fff176'},
                {'range': [750, 1000], 'color': '#4caf50'}],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 950}
        }
    ))
    fig.update_layout(height=400)
    return fig

def criar_grafico_entradas_saidas(df: pd.DataFrame) -> go.Figure:
    """Cria um gráfico de barras mensais de Entradas vs. Saídas."""
    if df.empty:
        return go.Figure().update_layout(title="Entradas vs. Saídas por Mês", annotations=[dict(text="Sem dados para o período selecionado.", showarrow=False)])
    
    df_temp = df.copy()
    df_temp['mes'] = pd.to_datetime(df_temp['created_at']).dt.to_period('M')
    resumo_mensal = df_temp.groupby(['mes', 'tipo'])['valor'].sum().unstack(fill_value=0).reset_index()
    resumo_mensal['mes'] = resumo_mensal['mes'].astype(str)
    
    colunas_presentes = [col for col in ['Entrada', 'Saída'] if col in resumo_mensal.columns]
    if not colunas_presentes:
        return go.Figure().update_layout(title="Entradas vs. Saídas por Mês", annotations=[dict(text="Sem dados de Entradas ou Saídas no período.", showarrow=False)])

    fig = px.bar(
        resumo_mensal, x='mes', y=colunas_presentes,
        title="Entradas vs. Saídas por Mês", labels={'value': 'Valor (R$)', 'mes': 'Mês'},
        color_discrete_map={'Entrada': '#4caf50', 'Saída': '#d32f2f'}, barmode='group'
    )
    fig.update_layout(legend_title_text='Tipo')
    return fig

def criar_grafico_top_categorias(df: pd.DataFrame) -> go.Figure:
    """Cria um gráfico de barras com as 10 principais categorias de despesa."""
    df_saidas = df[df['tipo'] == 'Saída']
    if df_saidas.empty:
        return go.Figure().update_layout(title="Top 10 Categorias de Despesa", annotations=[dict(text="Sem dados de saída no período selecionado.", showarrow=False)])
    
    top_10 = df_saidas.groupby('categoria')['valor'].sum().nlargest(10).sort_values(ascending=True)
    
    fig = px.bar(
        top_10, x=top_10.values, y=top_10.index, orientation='h',
        title="Top 10 Categorias de Despesa", labels={'x': 'Total Gasto (R$)', 'y': 'Categoria'},
        text=top_10.values,
    )
    fig.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
    fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    return fig


# --- 3. FLUXO PRINCIPAL DA PÁGINA ---
if 'access_token' not in st.session_state or not st.session_state['access_token']:
    st.error("⚠️ Você precisa fazer o login para acessar esta página.")
    st.switch_page("login.py")
    st.stop()

token = st.session_state.get('access_token')
df_original = carregar_transacoes(token)

if df_original is None or df_original.empty:
    st.warning("Não há dados de transações para exibir. Adicione algumas para começar!")
    st.stop()

st.title("🏠 Dashboard Principal")
st.markdown("Sua visão geral da saúde financeira.")

# --- Lógica de Callbacks para os filtros ---
def set_date_range(start, end):
    st.session_state.start_date = start
    st.session_state.end_date = end

def set_current_month():
    today = date.today()
    start = today.replace(day=1)
    set_date_range(start, today)

def set_last_month():
    today = date.today()
    first_day_current_month = today.replace(day=1)
    last_day_last_month = first_day_current_month - timedelta(days=1)
    first_day_last_month = last_day_last_month.replace(day=1)
    set_date_range(first_day_last_month, last_day_last_month)
    
def set_current_year():
    today = date.today()
    start = today.replace(month=1, day=1)
    set_date_range(start, today)

with st.expander("📅 Filtros e Períodos", expanded=True):
    # --- Inicialização do st.session_state para as datas ---
    datas_validas = df_original['created_at'].dropna()
    data_min_geral = datas_validas.min() if not datas_validas.empty else date.today()
    data_max_geral = datas_validas.max() if not datas_validas.empty else date.today()

    if 'start_date' not in st.session_state:
        st.session_state.start_date = data_min_geral
    if 'end_date' not in st.session_state:
        st.session_state.end_date = data_max_geral
    
    # --- Filtros Predefinidos ---
    st.markdown("**Filtros Rápidos de Período**")
    col_btn1, col_btn2, col_btn3, _ = st.columns([1, 1, 1, 3])
    col_btn1.button("Mês Vigente", on_click=set_current_month, use_container_width=True)
    col_btn2.button("Último Mês", on_click=set_last_month, use_container_width=True)
    col_btn3.button("Este Ano", on_click=set_current_year, use_container_width=True)

    st.divider()
    
    # --- Filtros Manuais e de Categoria/Tipo ---
    col_filtro1, col_filtro2, col_filtro3 = st.columns([2, 2, 2])
    
    start_date = col_filtro1.date_input("Data Inicial", key='start_date', min_value=data_min_geral, max_value=data_max_geral)
    end_date = col_filtro1.date_input("Data Final", key='end_date', min_value=data_min_geral, max_value=data_max_geral)

    tipo_selecionado = col_filtro2.radio(
        "Filtrar por Tipo",
        options=['Todas', 'Entrada', 'Saída'],
        horizontal=True,
        index=0
    )

    categorias_unicas = ['Todas'] + sorted(df_original['categoria'].dropna().unique().tolist())
    categoria_selecionada = col_filtro3.selectbox("Filtrar por Categoria", options=categorias_unicas)

# --- Aplicação dos filtros ---
df_filtrado = df_original[
    (df_original['created_at'] >= start_date) &
    (df_original['created_at'] <= end_date)
]

if tipo_selecionado != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['tipo'] == tipo_selecionado]
    
if categoria_selecionada != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['categoria'] == categoria_selecionada]

# --- 4. RENDERIZAÇÃO DO DASHBOARD ---
if df_filtrado.empty:
    st.info("Não há transações que correspondam aos filtros selecionados. Por favor, ajuste os filtros.")
    st.stop()

score_financeiro_placeholder = 785
st.plotly_chart(criar_grafico_velocimetro(score_financeiro_placeholder), use_container_width=True)
st.divider()

st.subheader("Resumo do Período Selecionado")
total_entradas = df_filtrado[df_filtrado['tipo'] == 'Entrada']['valor'].sum() if 'Entrada' in df_filtrado['tipo'].unique() else 0
total_saidas = df_filtrado[df_filtrado['tipo'] == 'Saída']['valor'].sum()
valor_net = total_entradas - total_saidas

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total de Entradas 🟢", f"R$ {total_entradas:,.2f}")
kpi2.metric("Total de Saídas 🔴", f"R$ {total_saidas:,.2f}")
kpi3.metric("Valor Líquido (NET) 🔵", f"R$ {valor_net:,.2f}")
st.divider()

st.subheader("Análise Detalhada")
col_grafico1, col_grafico2 = st.columns(2)
with col_grafico1:
    st.plotly_chart(criar_grafico_entradas_saidas(df_filtrado), use_container_width=True)
with col_grafico2:
    st.plotly_chart(criar_grafico_top_categorias(df_filtrado), use_container_width=True)
st.divider()

st.markdown("© 2025 Radar Financeiro. Todos os direitos reservados.")