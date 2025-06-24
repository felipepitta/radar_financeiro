# ==============================================================================
# ARQUIVO: app/schemas.py
# FUNÇÃO: Define o "contrato" de dados da API. Valida os dados que entram
#         e formata os dados que saem.
# ==============================================================================
from pydantic import BaseModel, EmailStr
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

# -- Schemas de Autenticação --
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    # Schema para a resposta do nosso endpoint de login
    user: dict
    session: dict

# -- Schemas de Transação --
class Transaction(BaseModel):
    id: int
    created_at: datetime
    item: Optional[str] = None
    valor: Optional[Decimal] = None
    categoria: Optional[str] = None

    class Config:
        from_attributes = True