import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Form, Depends, HTTPException
from twilio.twiml.messaging_response import MessagingResponse
import os
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List, Optional

# Importações limpas
from . import models, schemas, ia
from .database import SessionLocal, engine, get_db 

load_dotenv()

# Cria as tabelas (OK para desenvolvimento)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Radar Financeiro API",
    description="API para gerenciar transações financeiras e interagir com IA."
)

@app.post("/webhook/twilio")
async def webhook_twilio(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint com depuração aprimorada para o banco de dados.
    """
    try:
        form_data = await request.form()
        message_body = form_data.get("Body", "")
        sender_id = form_data.get("From", "")

        print(f"MENSAGEM RECEBIDA de {sender_id}: {message_body}")
        
        print("PASSO 1: Preparando para salvar no banco de dados...")
        new_transaction = models.Transaction(
            sender_id=sender_id,
            message_body=message_body
        )
        db.add(new_transaction)
        print("PASSO 2: Objeto adicionado à sessão. Tentando o commit...")
        
        db.commit()
        print("PASSO 3: Commit executado SEM ERRO APARENTE. Tentando o refresh...")

        db.refresh(new_transaction)
        print(f"PASSO 4: SUCESSO REAL! Transação salva no DB com ID: {new_transaction.id}")

        twiml_response = MessagingResponse()
        twiml_response.message(f"Radar Financeiro recebeu e SALVOU: '{message_body}'.")

        # --- NOVA LINHA DE DEBUG ---
        print("--- TwiML Gerado para Resposta ---")
        print(str(twiml_response))
        print("---------------------------------")
        # ---------------------------

        return Response(content=str(twiml_response), media_type="application/xml")

    except Exception as e:
        print(f"--- ERRO CRÍTICO NO BLOCO TRY ---")
        print(f"TIPO DE ERRO: {type(e)}")
        print(f"MENSAGEM DO ERRO: {e}")
        print("--- EXECUTANDO ROLLBACK ---")
        db.rollback()
        return Response(content="Ocorreu um erro interno no webhook.", status_code=500)

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
    # A parte de encontrar/criar usuário continua igual
    usuario = db.query(models.Usuario).filter(models.Usuario.telefone == msg.telefone).first()
    if not usuario:
        usuario = models.Usuario(telefone=msg.telefone, nome=f"Usuário {msg.telefone}")
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    texto = msg.mensagem.lower().strip()

    # Bloco try/except limpo, voltando a capturar apenas erros de valor/índice
    try:
        if texto.startswith("receita:"):
            partes = texto.replace("receita:", "").strip().split()
            if len(partes) < 2:
                raise ValueError("Formato inválido. Use: receita <valor> <descrição>")
            valor_str = partes[0].replace(",",".")
            valor = Decimal(valor_str)
            descricao = " ".join(partes[1:])
            novo_evento = models.Evento(usuario_id=usuario.id, tipo="receita", valor=valor, descricao=descricao)
            db.add(novo_evento)
            db.commit()
            return {"resposta": f"Receita de R$ {valor:.2f} ({descricao}) registrada."}

        elif texto.startswith("gasto:"):
            partes = texto.replace("gasto:", "").strip().split()
            if len(partes) < 2:
                raise ValueError("Formato inválido. Use: gasto <valor> <descrição>")
            valor_str = partes[0].replace(",",".")
            valor = Decimal(valor_str)
            descricao = " ".join(partes[1:])
            novo_evento = models.Evento(usuario_id=usuario.id, tipo="gasto", valor=valor, descricao=descricao)
            db.add(novo_evento)
            db.commit()
            return {"resposta": f"Gasto de R$ {valor:.2f} ({descricao}) registrado."}
        
        else: # Se não for um comando, vai para a IA
            resposta_ia = await ia.consulta_ia(telefone=usuario.telefone, prompt=texto)
            return {"resposta": resposta_ia}

    except (ValueError, IndexError) as e:
        # Retorna o erro de formato para o usuário de forma amigável
        return {"resposta": f"Erro ao processar seu comando: {e}. Tente novamente."}

# =================================================================
# Bloco para rodar em desenvolvimento (AGORA NO FINAL DE TUDO)
# =================================================================
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)