# app/schemas.py (versão final e completa)

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

# -------------------------------------------------------------------
# SCHEMAS PARA EVENTOS
# -------------------------------------------------------------------

class EventoBase(BaseModel):
    """Campos que um evento sempre terá."""
    tipo: str
    descricao: str
    valor: Optional[Decimal] = None

class EventoCreate(EventoBase):
    """Schema usado para criar um novo evento (não precisamos no momento, mas é uma boa prática)."""
    pass

class Evento(EventoBase):
    """
    Este é o schema para LER um evento. É o que será retornado pela API.
    Ele inclui campos que são gerados pelo banco de dados, como 'id'.
    """
    id: int
    usuario_id: int
    criado_em: datetime

    class Config:
        # Permite que o Pydantic leia os dados diretamente de modelos ORM (como os do SQLAlchemy).
        from_attributes = True

# Este schema define como uma transação será representada ao sair da nossa API.
# Ele funciona como um filtro e um validador de dados.
class Transaction(BaseModel):
    id: int
    message_body: str
    created_at: datetime
    item: Optional[str] = None
    valor: Optional[Decimal] = None
    categoria: Optional[str] = None

    # Configuração essencial para que o Pydantic consiga ler os dados
    # diretamente de um objeto do SQLAlchemy (nosso 'models.Transaction').
    class Config:
        from_attributes = True # Em versões antigas do Pydantic, isso era orm_mode = True


# -------------------------------------------------------------------
# SCHEMAS PARA USUÁRIOS
# -------------------------------------------------------------------

class UsuarioBase(BaseModel):
    """Campos base de um usuário."""
    telefone: str
    nome: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    """Schema para criar um novo usuário."""
    pass

class Usuario(UsuarioBase):
    """Schema para LER um usuário, incluindo a lista de seus eventos."""
    id: int
    # Importante: A lista de eventos usará o schema 'Evento' que definimos acima.
    eventos: List[Evento] = []

    class Config:
        from_attributes = True
        
# -------------------------------------------------------------------
# SCHEMA PARA WEBHOOK (O que já tínhamos)
# -------------------------------------------------------------------

class WebhookIn(BaseModel):
    telefone: str
    mensagem: str