# ==============================================================================
# ARQUIVO: app/dependencies.py
# FUNÇÃO: Centraliza a criação de clientes e dependências de autenticação. (v2.1 - Debug)
# ==============================================================================
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from gotrue.errors import AuthApiError

from . import models
from .database import get_db
from .config import settings
from supabase import create_client, Client


supabase_backend_client: Client = create_client(
    settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """
    Dependência de autenticação com depuração detalhada.
    """
    try:
        print("\n--- DEBUG [get_current_user]: Iniciando validação de token.")
        # 1. Valida o token com o Supabase
        user_auth_data = supabase_backend_client.auth.get_user(token)
        
        if not user_auth_data:
            print("--- DEBUG [get_current_user]: ERRO! Supabase não validou o token.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = user_auth_data.user.id
        print(f"--- DEBUG [get_current_user]: Token válido. ID do Supabase: {user_id}")
        
        # 2. Usa o ID do Supabase para buscar nosso perfil de usuário local
        print(f"--- DEBUG [get_current_user]: Buscando perfil no banco de dados local com o ID acima...")
        user_profile = db.query(models.User).filter(models.User.id == user_id).first()
        
        if user_profile is None:
            print(f"--- DEBUG [get_current_user]: FALHA! Perfil com ID {user_id} não encontrado no banco de dados local. Retornando 404.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found in our local database.",
            )
            
        print(f"--- DEBUG [get_current_user]: SUCESSO! Perfil local encontrado para o usuário: {user_profile.email}")
        return user_profile

    except AuthApiError as e:
        print(f"--- DEBUG [get_current_user]: ERRO! O Supabase retornou um AuthApiError: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(f"--- DEBUG [get_current_user]: ERRO INESPERADO! {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno na validação do usuário.")