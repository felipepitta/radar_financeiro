# -----------------------------------------------------------------------------
# login.py - Ponto de Entrada do Dashboard e Autenticação
# -----------------------------------------------------------------------------
# Este script é a "porta da frente" do nosso dashboard. Ele gerencia o estado
# de login do usuário e apresenta os formulários de login e cadastro.
# Nenhuma outra página é acessível sem passar por esta autenticação.
# -----------------------------------------------------------------------------

# 1. Imports: Bibliotecas de terceiros e padrão do Python
import streamlit as st
import requests
import os
from dotenv import load_dotenv

# 2. Configurações Iniciais e Carregamento de Variáveis
# Carrega as variáveis de ambiente do arquivo .env (ex: API_URL)
load_dotenv()

# Configura o título da aba do navegador e o layout da página
st.set_page_config(page_title="Radar Financeiro - Login", layout="centered")

# URL base da nossa API FastAPI. Centralizada aqui para fácil manutenção.
API_URL = "http://127.0.0.1:8000"

# --- Título Principal ---
st.title("Radar Financeiro 📈")

# -----------------------------------------------------------------------------
# 3. Lógica Principal de Autenticação
# -----------------------------------------------------------------------------
# st.session_state é a "memória" do Streamlit para cada sessão de usuário.
# Verificamos se já guardamos o email do usuário para saber se ele está logado.
if 'user_email' in st.session_state:
    # Se o usuário JÁ ESTÁ LOGADO, exibe a tela de boas-vindas.
    st.header("Login efetuado com sucesso!")
    st.success(f"Bem-vindo, {st.session_state.user_email}!")
    st.markdown("👈 Você já pode navegar para as outras páginas na barra lateral.")
    
    # Botão de Logout para limpar a sessão e voltar à tela de login.
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
else:
    # Se o usuário NÃO ESTÁ LOGADO, mostra as abas de Login e Cadastro.
    login_tab, signup_tab = st.tabs(["Login", "Cadastre-se"])

    # --- Aba de Login ---
    with login_tab:
        # 'st.form' agrupa os campos e garante que todos sejam enviados juntos
        # com um único clique no botão.
        with st.form("login_form", clear_on_submit=True):
            st.markdown("##### Já tem uma conta?")
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")

            if submitted:
                try:
                    login_payload = {"email": email, "password": password}
                    # Usamos 'requests' para chamar nosso próprio endpoint de login no backend.
                    response = requests.post(f"{API_URL}/auth/login", json=login_payload)
                    # Se a API retornar um erro (4xx ou 5xx), a linha abaixo lança uma exceção.
                    response.raise_for_status()
                    
                    session_data = response.json()
                    
                    # Se o login for bem-sucedido, guardamos as informações na memória da sessão.
                    st.session_state.user_email = session_data['user']['email']
                    st.session_state.access_token = session_data['session']['access_token']
                    
                    # 'st.rerun()' força o script a rodar novamente. Como agora teremos 'user_email'
                    # na session_state, o bloco 'if' do topo será executado.
                    st.rerun()

                except requests.exceptions.HTTPError as e:
                    # Captura erros de login (ex: senha errada) e mostra a mensagem da API.
                    error_detail = e.response.json().get('detail', "Erro desconhecido.")
                    st.error(f"Erro no login: {error_detail}")
                except Exception as e:
                    st.error(f"Ocorreu um erro inesperado: {e}")

    # --- Aba de Cadastro ---
    with signup_tab:
        # CORREÇÃO: Todos os campos do formulário devem estar DENTRO do 'with st.form'.
        with st.form("signup_form", clear_on_submit=True):
            st.markdown("##### Novo por aqui?")
            name = st.text_input("Nome Completo", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Senha", type="password", key="signup_password")
            telefone = st.text_input("Telefone com DDD e 9 (ex: 5511999999999)", key="signup_telefone")
            submitted = st.form_submit_button("Criar Conta")
            
            if submitted:
                # Validação simples para garantir que todos os campos foram preenchidos.
                if not all([name, email, password, telefone]):
                    st.warning("Por favor, preencha todos os campos.")
                else:
                    try:
                        # Monta o payload para enviar para o nosso endpoint de cadastro.
                        signup_payload = {"email": email, "password": password, "phone": telefone, "name": name}
                        response = requests.post(f"{API_URL}/auth/signup", json=signup_payload)
                        response.raise_for_status()

                        st.success("Conta criada com sucesso! Por favor, faça o login na aba 'Login'.")
                    
                    except requests.exceptions.HTTPError as e:
                        # Captura erros de cadastro (ex: email já existe) e mostra a mensagem da API.
                        error_detail = e.response.json().get('detail', "Erro desconhecido.")
                        st.error(f"Erro no cadastro: {error_detail}")
                    except Exception as e:
                        st.error(f"Ocorreu um erro inesperado: {e}")