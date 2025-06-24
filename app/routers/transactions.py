# ==============================================================================
# ARQUIVO: app/routers/transactions.py
# FUNÇÃO: Contém os endpoints para manipular as transações.
# ==============================================================================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/users", tags=["Transactions"])

@router.get("/{telefone}/transactions", response_model=List[schemas.Transaction], summary="Lista as transações de um usuário")
def get_user_transactions(telefone: str, db: Session = Depends(get_db)):
    # Futuramente, este endpoint será protegido e pegará o usuário pelo token JWT.
    # Por enquanto, usamos o telefone normalizado.
    telefone_limpo = ''.join(filter(str.isdigit, telefone))
    if not telefone_limpo.startswith('55'):
        telefone_limpo = f"55{telefone_limpo}"
    sender_id_formatado = f"whatsapp:+{telefone_limpo}"
    
    transacoes = db.query(models.Transaction)\
                   .filter(models.Transaction.sender_id == sender_id_formatado)\
                   .order_by(models.Transaction.created_at.desc())\
                   .all()

    if not transacoes:
        raise HTTPException(status_code=404, detail="Nenhuma transação encontrada.")
    return transacoes