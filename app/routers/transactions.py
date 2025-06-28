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
from .auth import get_current_active_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])

print("--- SENSOR 1: Roteador de TRANSACTIONS definido com prefixo '/transactions'.")
# -----------------------------

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

@router.put("/{transaction_id}", response_model=schemas.TransactionUpdate)
def update_transaction(
    transaction_id: int, 
    payload: schemas.TransactionUpdate,
    db: Session = Depends(get_db),
    # AGORA VAI FUNCIONAR! FastAPI chamará o "porteiro" para cada requisição.
    current_user: models.User = Depends(get_current_active_user)
):
    # ... (o resto da função permanece igual)
    # 1. Busca a transação
    transaction_query = db.query(models.Transaction).filter(models.Transaction.id == transaction_id)
    db_transaction = transaction_query.first()

    # 2. Verifica se a transação existe
    if db_transaction is None:
        raise HTTPException(status_code=404, detail=f"Transaction with id {transaction_id} not found")

    # 3. VERIFICAÇÃO DE SEGURANÇA
    if db_transaction.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to perform requested action")

    # 4. Se tudo estiver certo, atualiza os campos do objeto com os dados do payload
    # Usamos o `dict()` do pydantic para pegar apenas os campos definidos no schema
    update_data = payload.dict()
    transaction_query.update(update_data, synchronize_session=False)
    
    # 5. Comita as alterações para o banco de dados
    db.commit()
    
    # 6. Retorna a transação atualizada
    return db_transaction