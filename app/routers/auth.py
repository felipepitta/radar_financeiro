# ==============================================================================
# ARQUIVO: app/routers/auth.py
# FUNÇÃO: Contém todos os endpoints relacionados à autenticação. (v2.0)
# ==============================================================================
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .. import schemas, models
from ..database import get_db
from ..dependencies import supabase_backend_client
import re

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", status_code=status.HTTP_201_CREATED, summary="Registra um novo usuário")
def auth_signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Cria um usuário na autenticação do Supabase e um perfil no banco de dados local.
    Trata erros de duplicação de e-mail/telefone de forma amigável.
    """
    try:
        # 1. Normaliza o telefone antes de qualquer operação
        phone_normalized = re.sub(r'\D', '', user_data.phone)
        if not phone_normalized.startswith("55"):
             phone_normalized = f"55{phone_normalized}"

        # 2. Cria o usuário no serviço de autenticação do Supabase
        auth_response = supabase_backend_client.auth.sign_up({
            "email": user_data.email, "password": user_data.password
        })
        new_user_id = auth_response.user.id
        
        # 3. Cria o perfil do usuário na nossa tabela 'users'
        user_profile = models.User(
            id=new_user_id,
            email=user_data.email,
            name=user_data.name,
            phone=phone_normalized
        )
        db.add(user_profile)
        db.commit()
        return {"message": "Usuário criado com sucesso!"}

    except IntegrityError as e:
        db.rollback()
        error_detail = str(e.orig)
        if "users_email_key" in error_detail or "ix_users_email" in error_detail:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este e-mail já está em uso.")
        if "users_phone_key" in error_detail or "ix_users_phone" in error_detail:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este telefone já está em uso.")
        # Se for outra violação de integridade, mostra um erro genérico
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao criar usuário devido a uma violação de dados.")
    
    except Exception as e:
        # Pega outros erros da API do Supabase, como senhas fracas
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=schemas.AuthResponse, summary="Autentica um usuário por e-mail ou telefone")
def auth_login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Autentica um usuário usando e-mail ou telefone.
    Busca o e-mail correspondente se o login for por telefone, pois o Supabase requer e-mail.
    """
    login_identifier = user_credentials.username
    
    # Se o identificador não for um e-mail, consideramos como telefone
    if "@" not in login_identifier:
        phone_normalized = re.sub(r'\D', '', login_identifier)
        if not phone_normalized.startswith("55"):
             phone_normalized = f"55{phone_normalized}"
        
        user_profile = db.query(models.User).filter(models.User.phone == phone_normalized).first()
        if not user_profile:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")
        
        # Encontramos o perfil, agora usamos o e-mail para autenticar no Supabase
        email_to_auth = user_profile.email
    else:
        # Se for um e-mail, usamos diretamente
        email_to_auth = login_identifier

    try:
        user_session = supabase_backend_client.auth.sign_in_with_password(
            {"email": email_to_auth, "password": user_credentials.password}
        )
        return user_session.dict()

    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")
    
# 1. Define o "esquema" de segurança.
# A URL 'auth/login' informa ao Swagger/FastAPI qual endpoint ele deve usar 
# para obter o token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_active_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    """
    Dependência para ser usada em endpoints protegidos.
    1. Extrai o token do cabeçalho da requisição.
    2. Valida o token com o Supabase para obter o usuário.
    3. Busca o perfil completo do usuário no nosso banco de dados local.
    4. Retorna o objeto do usuário ou lança uma exceção de não autorizado.
    """
    try:
        # 2. Valida o token com o Supabase. Se o token for inválido ou expirado,
        # o Supabase vai levantar uma exceção.
        user_data_from_supabase = supabase_backend_client.auth.get_user(token)
        user_id = user_data_from_supabase.user.id

        # 3. Busca o usuário correspondente em nosso banco de dados local
        user_profile = db.query(models.User).filter(models.User.id == user_id).first()

        if user_profile is None:
            # Caso raro: usuário existe no Supabase mas não no nosso DB
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")

        # 4. Retorna o perfil completo do usuário
        return user_profile

    except Exception:
        # Se a validação do Supabase falhar por qualquer motivo
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
