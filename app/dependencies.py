# ==============================================================================
# ARQUIVO: app/dependencies.py
# FUNÇÃO: Centraliza a criação de clientes e dependências de autenticação. (v2.0)
# ==============================================================================
# Imports do FastAPI e de segurança
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Imports do banco de dados e dos nossos modelos
from sqlalchemy.orm import Session
from .database import get_db
from . import models

# Imports dos serviços externos
from supabase import create_client, Client
from gotrue.errors import AuthApiError
from .config import settings

# --- SUA LÓGICA ORIGINAL (perfeita, sem alterações) ---
# Cliente do Supabase para operações de backend (usando a chave de serviço secreta)
supabase_backend_client: Client = create_client(
    settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY
)

# --- NOVA FUNCIONALIDADE (AUTENTICAÇÃO) ---

# 1. O "Guarda de Segurança" do FastAPI
# Ele sabe que deve procurar por um token no cabeçalho "Authorization".
# O 'tokenUrl' aponta para o nosso próprio endpoint de login em auth.py.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# 2. A Dependência Principal de Autenticação
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """
    Esta função é o nosso "verificador de identidade" reutilizável.
    1. Recebe um token da requisição (graças ao oauth2_scheme).
    2. Valida esse token com o Supabase.
    3. Usa o ID do usuário validado para buscar nosso perfil no banco de dados local.
    4. Retorna o objeto completo do nosso usuário (models.User).
    
    Qualquer endpoint que precisar de login, vai "depender" desta função.
    """
    try:
        # Valida o token com o Supabase para obter os dados do usuário autenticado
        user_auth_data = supabase_backend_client.auth.get_user(token)
        
        if not user_auth_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Não foi possível validar as credenciais",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Usa o ID do Supabase para buscar nosso perfil de usuário local
        user_id = user_auth_data.user.id
        user_profile = db.query(models.User).filter(models.User.id == user_id).first()
        
        if user_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de usuário não encontrado no nosso banco de dados.",
            )
            
        return user_profile

    except AuthApiError:
        # Se o token for inválido ou expirado, o Supabase levanta um AuthApiError
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )