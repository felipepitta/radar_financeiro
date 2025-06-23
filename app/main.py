# 1. Bibliotecas padrão do Python
import os
from dotenv import load_dotenv
from decimal import Decimal
from typing import List, Optional

# Carregamento do .env
load_dotenv()

# 2. Bibliotecas de terceiros (pip install)
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from twilio.twiml.messaging_response import MessagingResponse

# 3. Imports da nossa própria aplicação
from . import models, schemas, ia
from .database import SessionLocal, engine, get_db

# Cria as tabelas (OK para desenvolvimento)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Radar Financeiro API",
    description="API para gerenciar transações financeiras e interagir com IA."
)

@app.get("/users/{telefone}/transactions", response_model=List[schemas.Transaction])
def get_user_transactions(telefone: str, db: Session = Depends(get_db)):
    """
    Busca todas as transações de um usuário, normalizando o número de telefone
    para garantir a correspondência com o formato salvo pelo Twilio.
    """
    # --- Bloco de Normalização do Telefone ---
    # 1. Remove qualquer caractere não numérico que o usuário possa ter digitado (ex: '+', '-', ' ').
    telefone_limpo = ''.join(filter(str.isdigit, telefone))
    
    # 2. Garante que o número comece com o código do país (55).
    #    Isso lida com o caso do usuário digitar só o número local (ex: 119...).
    if not telefone_limpo.startswith('55'):
        telefone_limpo = f"55{telefone_limpo}"
    
    # 3. Monta o ID final no formato exato que o Twilio salva no banco de dados.
    sender_id_formatado = f"whatsapp:+{telefone_limpo}"
    
    print(f"Buscando transações para o sender_id NORMALIZADO: {sender_id_formatado}")
    # --- Fim do Bloco de Normalização ---

    # A query agora usa o ID formatado corretamente para a busca.
    transacoes = db.query(models.Transaction)\
                   .filter(models.Transaction.sender_id == sender_id_formatado)\
                   .order_by(models.Transaction.created_at.desc())\
                   .all()

    if not transacoes:
        # Se, mesmo após a normalização, não houver transações, retorna o erro 404.
        # O dashboard saberá como lidar com esta resposta.
        raise HTTPException(status_code=404, detail="Nenhuma transação encontrada para este usuário.")
        
    # Se encontrar, retorna a lista de transações. 
    # FastAPI cuidará da conversão para o formato JSON usando o nosso schema.
    return transacoes


@app.post("/webhook/twilio")
async def webhook_twilio(request: Request, db: Session = Depends(get_db)):
    """
    Recebe uma mensagem do Twilio, salva a transação bruta, a enriquece com dados da IA,
    e responde de forma inteligente para o usuário.
    """
    # Bloco Try/Except: Uma rede de segurança para capturar qualquer erro inesperado
    # que possa acontecer durante o processamento, evitando que a aplicação quebre.
    try:
        # --- 1. RECEPÇÃO E PARSE DA MENSAGEM ---
        # Pega os dados do formulário enviado pela Twilio.
        form_data = await request.form()
        message_body = form_data.get("Body", "Mensagem vazia")
        sender_id = form_data.get("From", "Número desconhecido")

        print(f"MENSAGEM RECEBIDA de {sender_id}: {message_body}")

        # --- 2. PERSISTÊNCIA INICIAL ---
        # Cria um registro inicial no banco de dados apenas com a mensagem bruta.
        # Isso garante que nenhuma mensagem seja perdida, mesmo que a IA falhe.
        raw_transaction = models.Transaction(
            sender_id=sender_id,
            message_body=message_body
        )
        db.add(raw_transaction)
        db.commit()
        db.refresh(raw_transaction) # Atualiza o objeto com o ID gerado pelo banco
        print(f"Transação bruta salva no DB com ID: {raw_transaction.id}")

        # --- 3. ANÁLISE COM INTELIGÊNCIA ARTIFICIAL ---
        # Envia o texto da mensagem para o nosso módulo de IA para extrair dados.
        print("Enviando para análise da IA...")
        dados_analisados = ia.analisar_transacao_simples(message_body)
        print(f"IA retornou dados estruturados: {dados_analisados}")

        # --- 4. ENRIQUECIMENTO DOS DADOS NO BANCO ---
        # Se a IA retornou dados válidos, atualizamos o registro no banco.
        if dados_analisados and not dados_analisados.get("error"):
            # Atualiza o objeto 'raw_transaction' com os novos dados
            raw_transaction.item = dados_analisados.get('item')
            raw_transaction.valor = dados_analisados.get('valor')
            raw_transaction.categoria = dados_analisados.get('categoria')
            
            db.commit() # Salva as novas informações no banco
            print(f"Transação ID {raw_transaction.id} enriquecida com dados da IA.")
        
        # --- 5. CONSTRUÇÃO DA RESPOSTA PARA O WHATSAPP ---
        twiml_response = MessagingResponse()
        
        # Se a IA funcionou, cria uma resposta rica para o usuário.
        if dados_analisados and not dados_analisados.get("error"):
            # CORREÇÃO DO BUG: Verifica se o valor é None ANTES de formatar.
            valor_recebido = dados_analisados.get('valor')
            valor_numerico = valor_recebido if valor_recebido is not None else 0.0
            
            item = dados_analisados.get('item', 'não identificado')
            categoria = dados_analisados.get('categoria', 'não identificada')
            
            resposta_formatada = (
                f"Entendido! ✅\n\n"
                f"Item: *{item}*\n"
                f"Valor: *R$ {valor_numerico:.2f}*\n"
                f"Categoria: *{categoria}*"
            )
            twiml_response.message(resposta_formatada)
        else:
            # Caso a IA falhe, envia uma resposta padrão.
            twiml_response.message("Recebido! Salvei sua anotação, mas não consegui extrair os detalhes.")

        # --- 6. ENVIO DA RESPOSTA ---
        # Retorna a resposta no formato XML que a Twilio espera.
        return Response(content=str(twiml_response), media_type="application/xml")

    except Exception as e:
        # Se qualquer erro não previsto ocorrer, ele será capturado aqui.
        print(f"--- ERRO CRÍTICO NO WEBHOOK ---")
        print(f"TIPO DE ERRO: {type(e).__name__}")
        print(f"MENSAGEM DO ERRO: {e}")
        db.rollback() # Desfaz qualquer alteração pendente no banco para manter a consistência.
        
        # Envia uma mensagem de erro amigável para o usuário.
        error_response = MessagingResponse()
        error_response.message("Desculpe, ocorreu um erro inesperado ao processar sua mensagem. Tente novamente.")
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