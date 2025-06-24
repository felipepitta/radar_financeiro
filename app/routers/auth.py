# ==============================================================================
# ARQUIVO: app/routers/auth.py
# FUNÇÃO: Contém todos os endpoints relacionados à autenticação.
# ==============================================================================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..dependencies import supabase_backend_client

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", summary="Registra um novo usuário")
def auth_signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # 1. Cria o usuário no serviço de autenticação do Supabase
        auth_response = supabase_backend_client.auth.sign_up({
            "email": user_data.email, "password": user_data.password
        })
        new_user_id = auth_response.user.id
        
        # 2. Cria o perfil do usuário na nossa tabela 'users'
        user_profile = models.User(
            id=new_user_id,
            email=user_data.email,
            name=user_data.name,
            phone=''.join(filter(str.isdigit, user_data.phone))
        )
        db.add(user_profile)
        db.commit()
        return {"message": "Usuário criado com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=schemas.AuthResponse, summary="Autentica um usuário")
def auth_login(user_credentials: schemas.UserLogin):
    try:
        user_session = supabase_backend_client.auth.sign_in_with_password(
            {"email": user_credentials.email, "password": user_credentials.password}
        )
        # Retorna a sessão completa, que contém o token de acesso
        return user_session.dict()
    except Exception as e:
        raise HTTPException(status_code=401, detail="Credenciais de login inválidas.")