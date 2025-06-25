# ==============================================================================
# ARQUIVO: app/routers/transactions.py
# FUNÇÃO: Contém os endpoints para manipular as transações.
# ==============================================================================
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("/me", response_model=List[schemas.Transaction], summary="Lista as transações do usuário autenticado")
def get_my_transactions(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Retorna uma lista de todas as transações pertencentes ao usuário
    identificado pelo token JWT.
    """
    transacoes = db.query(models.Transaction)\
                   .filter(models.Transaction.owner_id == current_user.id)\
                   .order_by(models.Transaction.created_at.desc())\
                   .all()

    return transacoes