# ==============================================================================
# ARQUIVO: app/main.py
# FUNÇÃO: O "Maestro". Monta a aplicação FastAPI e inclui todos os roteadores.
# ==============================================================================
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
load_dotenv()
from . import models
from .database import engine
from .routers import auth, transactions, webhook

# Cria as tabelas no banco de dados, se não existirem
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Radar Financeiro API",
    description="API para gerenciar transações financeiras, usuários e interagir com IA."
)

# ✅ --- FILTRO DE SEGURANÇA: EXCEPTION HANDLER ---
# Este bloco intercepta erros de validação antes de serem enviados.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler customizado para tratar erros de validação do Pydantic,
    removendo dados sensíveis como 'password' da resposta de erro.
    """
    error_details = exc.errors()
    modified_details = []
    for error in error_details:
        # Remove o campo 'input' para não expor nenhum dado do usuário
        if 'input' in error:
            del error['input']
        # Remove o campo 'url' que não é necessário para o usuário final
        if 'url' in error:
            del error['url']
        modified_details.append(error)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": modified_details},
    )

# Inclui os roteadores na aplicação principal
print("INFO: Incluindo roteador de autenticação...")
app.include_router(auth.router)
print("INFO: Incluindo roteador de transações...")
app.include_router(transactions.router)
print("INFO: Incluindo roteador de webhook...")
app.include_router(webhook.router)

@app.get("/", summary="Endpoint raiz da API")
def read_root():
    return {"status": "Radar Financeiro API está no ar e 100% refatorado!"}