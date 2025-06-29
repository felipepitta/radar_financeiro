from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pandas as pd

# ==================== SOLUÇÃO DEFINITIVA: IMPORTS ABSOLUTOS ====================
# Note que todos os imports agora começam com 'app.'
# Isso dá ao Python o caminho exato a partir da raiz do projeto, sem ambiguidades.

from app.dependencies import get_db, get_current_user
from app import crud
from app import schemas
from app import ia
# ==============================================================================

router = APIRouter(
    prefix="/ai",
    tags=["ai"],
    responses={404: {"description": "Not found"}},
)

class AIQuestion(BaseModel):
    question: str

@router.post("/ask", response_model=schemas.AIAnswer)
def ask_ai(
    ai_question: AIQuestion,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """
    Recebe uma pergunta, busca o histórico do usuário e consulta a IA.
    """
    transactions = crud.get_transactions_by_user(db, user_id=current_user.id)
    if not transactions:
        return {"answer": "Não encontrei dados de transações para analisar. Por favor, adicione alguns registros primeiro."}

    transactions_df = pd.DataFrame([t.__dict__ for t in transactions])
    transactions_csv = transactions_df[['created_at', 'description', 'valor', 'tipo', 'categoria']].to_csv(index=False)

    ai_response = ia.gerar_analise_financeira(
        historico_transacoes_csv=transactions_csv,
        pergunta_usuario=ai_question.question
    )

    return {"answer": ai_response}