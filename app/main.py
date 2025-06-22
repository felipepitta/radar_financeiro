import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import List, Optional

# Importações limpas
from . import models, schemas, ia
from .database import SessionLocal, engine

# Cria as tabelas (OK para desenvolvimento)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Radar Financeiro API",
    description="API para gerenciar transações financeiras e interagir com IA."
)

# =================================================================
# DEPENDÊNCIA: Gerenciador de Sessão do Banco de Dados
# Esta função garante que cada requisição tenha sua própria sessão
# e que ela seja FECHADA ao final, mesmo que ocorra um erro.
# =================================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =================================================================
# ENDPOINT PRINCIPAL: /webhook
# =================================================================
@app.post("/webhook", summary="Recebe e processa mensagens do usuário")
async def receber_mensagem(msg: schemas.WebhookIn, db: Session = Depends(get_db)):
    """
    Este endpoint é o ponto de entrada principal. Ele recebe uma mensagem,
    a processa como um comando (gasto, agenda) ou como uma pergunta para a IA.
    """
    
    # 1. Encontrar ou criar o usuário
    # A lógica de 'find-or-create' garante que sempre teremos um usuário para associar ao evento.
    usuario = db.query(models.Usuario).filter(models.Usuario.telefone == msg.telefone).first()
    if not usuario:
        usuario = models.Usuario(telefone=msg.telefone, nome=f"Usuário {msg.telefone}")
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    texto = msg.mensagem.lower().strip()

    # 2. Processamento de Comandos (forma segura)
    try:
        if texto.startswith("agenda:"):
            descricao = texto.replace("agenda:", "").strip()
            if not descricao:
                raise ValueError("A descrição da agenda não pode ser vazia.")
            
            # Cria o evento associado ao ID do usuário
            novo_evento = models.Evento(usuario_id=usuario.id, tipo="agenda", descricao=descricao)
            db.add(novo_evento)
            db.commit()
            return {"resposta": f"Lembrete agendado: '{descricao}'"}

        elif texto.startswith("gasto:"):
            partes = texto.replace("gasto:", "").strip().split()
            if len(partes) < 2:
                raise ValueError("Formato inválido. Use: gasto <valor> <descrição>")
            
            valor_str = partes[0].replace(",",".") # Aceita vírgula e ponto como decimal
            valor = Decimal(valor_str)
            descricao = " ".join(partes[1:])
            
            novo_evento = models.Evento(usuario_id=usuario.id, tipo="gasto", valor=valor, descricao=descricao)
            db.add(novo_evento)
            db.commit()
            return {"resposta": f"Gasto de R$ {valor:.2f} ({descricao}) registrado."}

    except (ValueError, IndexError) as e:
        # Se o comando do usuário for mal formatado, retorna um erro amigável.
        return {"resposta": f"Erro ao processar seu comando: {e}. Tente novamente."}

    # 3. Se não for um comando, consultar a IA
    resposta_ia = await ia.consulta_ia(telefone=usuario.telefone, prompt=texto)
    return {"resposta": resposta_ia}

# Bloco para rodar em desenvolvimento
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

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