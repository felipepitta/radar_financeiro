# ==============================================================================
# ARQUIVO: dashboard/login.py
# FUNÇÃO: A "porta da frente" do dashboard. Gerencia o login/cadastro.
# ==============================================================================
import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Radar Financeiro - Login", layout="centered")
API_URL = "http://127.0.0.1:8000"

st.title("Radar Financeiro 📈")

if 'user_email' in st.session_state:
    st.header("Login efetuado com sucesso!")
    st.success(f"Bem-vindo, {st.session_state.user_email}!")
    st.markdown("👈 Você já pode navegar para as outras páginas na barra lateral.")
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
else:
    login_tab, signup_tab = st.tabs(["Login", "Cadastre-se"])

    with login_tab:
        with st.form("login_form", clear_on_submit=True):
            st.markdown("##### Já tem uma conta?")
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")
            if submitted:
                try:
                    login_payload = {"email": email, "password": password}
                    response = requests.post(f"{API_URL}/auth/login", json=login_payload)
                    response.raise_for_status()
                    session_data = response.json()
                    
                    st.session_state.user_info = session_data['user']
                    st.session_state.user_email = session_data['user']['email']
                    st.session_state.access_token = session_data['session']['access_token']
                    
                    st.rerun()
                except requests.exceptions.HTTPError as e:
                    error_detail = e.response.json().get('detail', "Erro desconhecido.")
                    st.error(f"Erro no login: {error_detail}")
                except Exception as e:
                    st.error(f"Ocorreu um erro inesperado: {e}")

    with signup_tab:
        with st.form("signup_form", clear_on_submit=True):
            st.markdown("##### Novo por aqui?")
            name = st.text_input("Nome Completo", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Senha", type="password", key="signup_password")
            telefone = st.text_input("Telefone com DDD e 9 (ex: 5511999999999)", key="signup_telefone")
            submitted = st.form_submit_button("Criar Conta")
            
            if submitted:
                if not all([name, email, password, telefone]):
                    st.warning("Por favor, preencha todos os campos.")
                else:
                    try:
                        signup_payload = {"email": email, "password": password, "phone": telefone, "name": name}
                        response = requests.post(f"{API_URL}/auth/signup", json=signup_payload)
                        response.raise_for_status()
                        st.success("Conta criada com sucesso! Por favor, faça o login na aba 'Login'.")
                    except requests.exceptions.HTTPError as e:
                        error_detail = e.response.json().get('detail', "Erro desconhecido.")
                        st.error(f"Erro no cadastro: {error_detail}")
                    except Exception as e:
                        st.error(f"Ocorreu um erro inesperado: {e}")