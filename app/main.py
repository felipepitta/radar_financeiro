# ==============================================================================
# ARQUIVO: app/main.py
# FUNÇÃO: O "Maestro". Monta a aplicação FastAPI e inclui todos os roteadores.
# ==============================================================================
import sys
import os

# --- CORREÇÃO DEFINITIVA: O GPS DEVE SER LIGADO PRIMEIRO! ---
# Colocamos este bloco no TOPO ABSOLUTO do arquivo.
# Ele ajusta o "mapa" do Python ANTES que qualquer import do nosso app seja tentado.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# -------------------------------------------------------------

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Agora os outros imports podem ser feitos com segurança
from app import models
from app.database import engine
from app.routers import auth, transactions, webhook, ai

# Carrega as variáveis de ambiente do .env
load_dotenv()

# Cria as tabelas no banco de dados, se não existirem
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Radar Financeiro API",
    description="API para gerenciar transações financeiras, usuários e interagir com IA."
)

# ✅ --- FILTRO DE SEGURANÇA: EXCEPTION HANDLER ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler customizado para tratar erros de validação do Pydantic.
    """
    error_details = exc.errors()
    modified_details = []
    for error in error_details:
        if 'input' in error:
            del error['input']
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
print("INFO: Incluindo roteador de IA...")
app.include_router(ai.router)

@app.get("/", summary="Endpoint raiz da API")
def read_root():
    return {"status": "Radar Financeiro API está no ar e 100% operacional!"}

@app.on_event("startup")
def print_all_routes():
    """Na inicialização, imprime uma lista de todas as rotas registradas."""
    print("\n--- ROTAS REGISTRADAS NA APLICAÇÃO ---")
    for route in app.routes:
        if hasattr(route, "methods"):
            print(f"Path: {route.path}, Methods: {route.methods}, Name: {route.name}")
        else:
            print(f"Path: {route.path}, Name: {type(route).__name__}")
    print("----------------------------------------\n")