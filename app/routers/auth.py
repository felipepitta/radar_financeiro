# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..dependencies import supabase_backend_client

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", summary="Registra um novo usuário")
def auth_signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Cria um usuário no Supabase Auth e, em caso de sucesso, cria um perfil
    correspondente em nossa tabela pública 'users'.
    """
    try:
        # CORREÇÃO: Adicionamos o 'options' de volta para salvar o telefone
        # nos metadados do usuário no Supabase Auth, além de nossa tabela.
        auth_response = supabase_backend_client.auth.sign_up({
            "email": user_data.email, 
            "password": user_data.password,
            "options": {
                "data": {
                    "phone": ''.join(filter(str.isdigit, user_data.phone))
                }
            }
        })
        
        new_user_id = auth_response.user.id

        # A lógica de salvar em nossa tabela 'users' está perfeita.
        user_profile = models.User(
            id=new_user_id,
            email=user_data.email,
            name=user_data.name,
            phone=''.join(filter(str.isdigit, user_data.phone)) # Salvamos o telefone aqui também
        )
        db.add(user_profile)
        db.commit()
        
        print(f"Perfil de usuário criado com sucesso para ID: {new_user_id}")
        return {"message": "Usuário criado com sucesso!"}
        
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", summary="Autentica um usuário")
def auth_login(user_credentials: schemas.UserLogin):
    try:
        user_session = supabase_backend_client.auth.sign_in_with_password(
            {"email": user_credentials.email, "password": user_credentials.password}
        )
        return {"user": user_session.user.dict(), "session": user_session.session.dict()}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Credenciais de login inválidas.")