# ==============================================================================
# ARQUIVO: app/main.py
# FUNÇÃO: O "Maestro". Monta a aplicação FastAPI e inclui todos os roteadores.
# ==============================================================================
from fastapi import FastAPI
from . import models
from .database import engine
from .routers import auth, transactions, webhook

# Cria as tabelas no banco de dados, se não existirem
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Radar Financeiro API",
    description="API para gerenciar transações financeiras, usuários e interagir com IA."
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