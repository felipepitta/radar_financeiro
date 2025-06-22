import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List, Optional

# Importações limpas
from . import models, schemas, ia
from .database import SessionLocal, engine

load_dotenv()

# Cria as tabelas (OK para desenvolvimento)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Radar Financeiro API",
    description="API para gerenciar transações financeiras e interagir com IA."
)

# =================================================================
# DEPENDÊNCIA: Gerenciador de Sessão do Banco de Dados
# =================================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =================================================================
# ENDPOINT DE LEITURA: /users/{telefone}/events
# (MOVEMOS ELE PARA CIMA, PARA O LUGAR CORRETO)
# =================================================================
@app.get("/users/{telefone}/events", response_model=List[schemas.Evento], summary="Lista todos os eventos de um usuário específico")
def get_user_events(telefone: str, db: Session = Depends(get_db)):
    """
    Busca um usuário pelo telefone e retorna todos os seus eventos.
    O 'response_model' garante que a saída seja uma lista de eventos
    formatada segundo o schema 'schemas.Evento'.
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.telefone == telefone).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # A lógica interna não muda. O FastAPI usa o response_model para fazer a conversão.
    return usuario.eventos

# =================================================================
# ENDPOINT DE ESCRITA: /webhook
# =================================================================
@app.post("/webhook", summary="Recebe e processa mensagens do usuário")
async def receber_mensagem(msg: schemas.WebhookIn, db: Session = Depends(get_db)):
    # ... (a parte de encontrar ou criar o usuário continua igual)
    usuario = db.query(models.Usuario).filter(models.Usuario.telefone == msg.telefone).first()
    if not usuario:
        usuario = models.Usuario(telefone=msg.telefone, nome=f"Usuário {msg.telefone}")
        db.add(usuario)
        # O commit aqui é para o usuário. Vamos adicionar um print também.
        try:
            db.commit()
            db.refresh(usuario)
            print(f"--- DEBUG: Usuário {usuario.telefone} criado/encontrado com ID: {usuario.id} ---")
        except Exception as e:
            db.rollback()
            print(f"--- ERRO AO CRIAR/SALVAR USUÁRIO: {e} ---")
            raise HTTPException(status_code=500, detail=f"Erro de banco de dados ao salvar usuário: {e}")

    texto = msg.mensagem.lower().strip()

    # Vamos modificar o bloco try/except do processamento de comandos
    try:
        # Adicione aqui o processamento do comando 'receita:'
        if texto.startswith("receita:"):
            partes = texto.replace("receita:", "").strip().split()
            if len(partes) < 2:
                raise ValueError("Formato inválido. Use: receita <valor> <descrição>")
            
            valor_str = partes[0].replace(",",".")
            valor = Decimal(valor_str)
            descricao = " ".join(partes[1:])
            
            print("--- DEBUG: Objeto RECEITA criado. Pronto para adicionar. ---")
            novo_evento = models.Evento(usuario_id=usuario.id, tipo="receita", valor=valor, descricao=descricao)
            
            db.add(novo_evento)
            print("--- DEBUG: db.add(novo_evento) para RECEITA executado. ---")
            
            db.commit()
            print("--- DEBUG: db.commit() para RECEITA executado! O dado DEVE estar no banco. ---")
            
            return {"resposta": f"Receita de R$ {valor:.2f} ({descricao}) registrada."}

        elif texto.startswith("gasto:"):
            partes = texto.replace("gasto:", "").strip().split()
            if len(partes) < 2:
                raise ValueError("Formato inválido. Use: gasto <valor> <descrição>")
            
            valor_str = partes[0].replace(",",".")
            valor = Decimal(valor_str)
            descricao = " ".join(partes[1:])
            
            print("--- DEBUG: Objeto GASTO criado. Pronto para adicionar. ---")
            novo_evento = models.Evento(usuario_id=usuario.id, tipo="gasto", valor=valor, descricao=descricao)
            
            db.add(novo_evento)
            print("--- DEBUG: db.add(novo_evento) para GASTO executado. ---")
            
            db.commit()
            print("--- DEBUG: db.commit() para GASTO executado! O dado DEVE estar no banco. ---")
            
            return {"resposta": f"Gasto de R$ {valor:.2f} ({descricao}) registrado."}

        # ... (a parte do 'agenda:' e da IA pode continuar aqui) ...
        else:
             resposta_ia = await ia.consulta_ia(telefone=usuario.telefone, prompt=texto)
             return {"resposta": resposta_ia}

    # MUDANÇA IMPORTANTE: Capturando QUALQUER exceção
    except Exception as e:
        print(f"--- ERRO CAPTURADO! A TRANSAÇÃO SERÁ REVERTIDA. ERRO: {e} ---")
        db.rollback()  # Desfaz a transação explicitamente
        # Retorna o erro real para o dashboard, para que ele também mostre o erro.
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {e}")

# =================================================================
# Bloco para rodar em desenvolvimento (AGORA NO FINAL DE TUDO)
# =================================================================
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)