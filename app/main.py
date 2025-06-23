# 1. Bibliotecas padrão do Python
import os
from decimal import Decimal
from typing import List, Optional

# (linha em branco)

# 2. Bibliotecas de terceiros (pip install)
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from twilio.twiml.messaging_response import MessagingResponse

# (linha em branco)

# 3. Imports da nossa própria aplicação
from . import models, schemas, ia
from .database import SessionLocal, engine, get_db

# Carregamento do .env
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
    Recebe uma mensagem do Twilio, salva no banco, analisa com IA e responde.
    """
    try:
        # 1. Receber e processar a mensagem do usuário
        form_data = await request.form()
        message_body = form_data.get("Body", "Mensagem vazia")
        sender_id = form_data.get("From", "Número desconhecido")

        print(f"MENSAGEM RECEBIDA de {sender_id}: {message_body}")

        # 2. Salvar a transação bruta no banco de dados
        raw_transaction = models.Transaction(
            sender_id=sender_id,
            message_body=message_body
        )
        db.add(raw_transaction)
        db.commit()
        db.refresh(raw_transaction)
        print(f"Transação bruta salva no DB com ID: {raw_transaction.id}")

        # 3. Enviar o texto para análise da Inteligência Artificial
        print("Enviando para análise da IA...")
        dados_analisados = ia.analisar_transacao(message_body)
        print(f"IA retornou dados estruturados: {dados_analisados}")

        # 4. Construir a resposta para o usuário
        twiml_response = MessagingResponse()
        
        # Cria uma resposta mais inteligente para o usuário, se a IA funcionou
        if dados_analisados and not dados_analisados.get("error"):
            item = dados_analisados.get('item', 'não identificado')
            valor = dados_analisados.get('valor', 0.0)
            categoria = dados_analisados.get('categoria', 'não identificada')
            
            resposta_formatada = (
                f"Entendido! ✅\n"
                f"Item: {item}\n"
                f"Valor: R$ {valor:.2f}\n"
                f"Categoria: {categoria}"
            )
            twiml_response.message(resposta_formatada)
        else:
            # Resposta padrão se a IA falhar ou não entender
            twiml_response.message("Recebido! Salvei sua anotação, mas não consegui extrair os detalhes.")

        # 5. Enviar a resposta final para a Twilio
        return Response(content=str(twiml_response), media_type="application/xml")

    except Exception as e:
        print(f"--- ERRO CRÍTICO NO WEBHOOK ---")
        print(f"TIPO DE ERRO: {type(e).__name__}")
        print(f"MENSAGEM DO ERRO: {e}")
        db.rollback() # Garante que a transação seja desfeita em caso de erro
        
        # Envia uma resposta de erro genérica para a Twilio
        error_response = MessagingResponse()
        error_response.message("Desculpe, ocorreu um erro ao processar sua mensagem.")
        return Response(content=str(error_response), media_type="application/xml")

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