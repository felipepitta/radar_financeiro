# app/schemas.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from decimal import Decimal
from typing import Optional

# -- Schemas de Autenticação --
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# -- Schemas de Transação --
class Transaction(BaseModel):
    id: int
    created_at: datetime
    item: Optional[str] = None
    valor: Optional[Decimal] = None
    categoria: Optional[str] = None

    class Config:
        from_attributes = True