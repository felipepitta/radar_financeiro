# ==============================================================================
# ARQUIVO: dashboard/login.py
# FUNÇÃO: A "porta da frente" do dashboard. Gerencia o login/cadastro.
# ==============================================================================
import streamlit as st
import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Radar Financeiro - Login", layout="centered", initial_sidebar_state="collapsed")
API_URL = "http://127.0.0.1:8000"

# --- FUNÇÃO DE LOGOUT ---
def logout():
    """Limpa o session_state e força o rerun para deslogar o usuário."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- LAYOUT PRINCIPAL ---
st.title("Radar Financeiro 📈")

# Se o usuário já está logado
if 'access_token' in st.session_state:
    with st.container(border=True):
        st.header(f"Bem-vindo(a) de volta!")
        user_name = st.session_state.get('user_name', 'Usuário')
        st.success(f"Você está logado como **{user_name}**.")
        st.markdown("👈 Use a barra lateral para navegar pelo sistema.")
        if st.button("Logout", use_container_width=True):
            logout()
else:
    # Abas de Login e Cadastro
    login_tab, signup_tab = st.tabs(["Login", "Cadastre-se"])

    # --- ABA DE LOGIN ---
    with login_tab:
        with st.form("login_form"):
            st.markdown("##### Já tem uma conta?")
            username = st.text_input("E-mail ou Telefone")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)
            
            if submitted:
                if not all([username, password]):
                    st.warning("Por favor, preencha todos os campos.")
                else:
                    try:
                        login_payload = {"username": username, "password": password}
                        response = requests.post(f"{API_URL}/auth/login", json=login_payload)
                        
                        if response.status_code == 200:
                            session_data = response.json()
                            st.session_state.user_name = session_data['user']['user_metadata'].get('name', 'Usuário')
                            st.session_state.user_email = session_data['user']['email']
                            st.session_state.access_token = session_data['session']['access_token']
                            st.rerun()
                        else:
                            error_detail = response.json().get('detail', "Erro desconhecido.")
                            st.error(f"Erro no login: {error_detail}")

                    except requests.exceptions.RequestException:
                        st.error("Não foi possível conectar ao servidor. Tente novamente mais tarde.")

    # --- ABA DE CADASTRO ---
    with signup_tab:
        with st.form("signup_form"):
            st.markdown("##### Novo por aqui?")
            name = st.text_input("Nome Completo", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Senha", type="password", key="signup_password")
            telefone = st.text_input("Telefone com DDD (ex: 11999999999)", key="signup_telefone")
            submitted = st.form_submit_button("Criar Conta", use_container_width=True)
            
            if submitted:
                if not all([name, email, password, telefone]):
                    st.warning("Por favor, preencha todos os campos.")
                else:
                    try:
                        # Normalização do telefone no frontend para feedback rápido se necessário
                        # A normalização final e mais segura é feita no backend
                        numeros = re.sub(r'\D', '', telefone)
                        if not (10 <= len(numeros) <= 11):
                             st.error("Formato de telefone inválido. Use apenas números, incluindo DDD.")
                        else:
                            signup_payload = {"email": email, "password": password, "phone": telefone, "name": name}
                            response = requests.post(f"{API_URL}/auth/signup", json=signup_payload)
                            
                            if response.status_code == 201:
                                st.success("Conta criada com sucesso! Por favor, faça o login na aba 'Login'.")
                            else:
                                # A API agora retorna uma mensagem amigável!
                                error_detail = response.json().get('detail', "Erro desconhecido.")
                                st.error(f"Erro no cadastro: {error_detail}")

                    except requests.exceptions.RequestException:
                        st.error("Não foi possível conectar ao servidor. Tente novamente mais tarde.")