import streamlit as st
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="Radar Financeiro - Login", layout="centered")

# --- Conexão com Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Credenciais do Supabase não configuradas. Verifique o .env!")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Lógica de Autenticação ---
st.title("Radar Financeiro 📈")

if 'user' in st.session_state:
    st.header("Login efetuado com sucesso!")
    st.success(f"Bem-vindo, {st.session_state.user.email}!")
    st.markdown("👈 Navegue para a página **Home** na barra lateral para começar.")
    if st.button("Logout"):
        del st.session_state.user
        st.rerun()
else:
    login_tab, signup_tab = st.tabs(["Login", "Cadastre-se"])

    with login_tab:
        # (O código do formulário de login continua o mesmo de antes)
        with st.form("login_form"):
             st.markdown("##### Já tem uma conta?")
             email = st.text_input("Email")
             password = st.text_input("Senha", type="password")
             submitted = st.form_submit_button("Entrar")
             if submitted:
                 try:
                     user_session = supabase.auth.sign_in_with_password({"email": email, "password": password})
                     st.session_state.user = user_session.user
                     st.rerun()
                 except Exception as e:
                     st.error(f"Erro no login: {e}")

    with signup_tab:
        # (O código do formulário de cadastro continua o mesmo de antes)
        with st.form("signup_form"):
             st.markdown("##### Novo por aqui?")
             email = st.text_input("Email", key="signup_email")
             password = st.text_input("Senha", type="password", key="signup_password")
             telefone = st.text_input("Telefone com DDD e 9 (ex: 5511999999999)", key="signup_telefone")
             submitted = st.form_submit_button("Criar Conta")
             if submitted:
                 if not telefone or not email or not password:
                     st.warning("Por favor, preencha todos os campos.")
                 else:
                     try:
                         new_user = supabase.auth.sign_up({
                             "email": email, "password": password,
                             "options": {"data": {"phone": ''.join(filter(str.isdigit, telefone))}}
                         })
                         st.success("Conta criada! Se o email for válido, você receberá uma confirmação. Por favor, faça o login na outra aba.")
                     except Exception as e:
                         st.error(f"Erro no cadastro: {e}")