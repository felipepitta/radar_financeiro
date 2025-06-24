# -----------------------------------------------------------------------------
# main.py - Ponto de Entrada Principal da API FastAPI
# -----------------------------------------------------------------------------
# Este arquivo define a aplicação FastAPI, inicializa as conexões
# e declara todos os endpoints (rotas) da nossa API.
# -----------------------------------------------------------------------------

# 1. Imports de Bibliotecas
# Bibliotecas padrão do Python
import os
from typing import List

# Bibliotecas de terceiros
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from sqlalchemy.orm import Session
from supabase import create_client, Client
from twilio.twiml.messaging_response import MessagingResponse

# Imports da nossa própria aplicação
from . import models, schemas, ia
from .database import engine, get_db

# -----------------------------------------------------------------------------
# 2. Configuração e Inicialização da Aplicação
# -----------------------------------------------------------------------------

# Carrega as variáveis de ambiente do arquivo .env no início de tudo.
load_dotenv()

# Inicializa o cliente do Supabase para operações de backend (com a chave de serviço).
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase_backend_client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Garante que todas as tabelas definidas em 'models.py' sejam criadas no banco
# de dados quando a aplicação inicia, caso ainda não existam.
models.Base.metadata.create_all(bind=engine)

# Cria a instância principal da aplicação FastAPI.
app = FastAPI(
    title="Radar Financeiro API",
    description="API para gerenciar transações financeiras, usuários e interagir com IA."
)

# -----------------------------------------------------------------------------
# 3. Endpoints de Autenticação
# -----------------------------------------------------------------------------

@app.post("/auth/signup", summary="Registra um novo usuário")
def auth_signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Cria um usuário no Supabase Auth e, em caso de sucesso, cria um perfil
    correspondente na nossa tabela pública 'users'.
    """
    print(f"Recebida solicitação de cadastro para: {user_data.email}")
    try:
        # Cria o usuário no serviço de autenticação
        auth_response = supabase_backend_client.auth.sign_up({
            "email": user_data.email, "password": user_data.password,
            "options": {"data": {"phone": ''.join(filter(str.isdigit, user_data.phone))}}
        })
        
        # Se o usuário foi criado no Auth, pega o ID dele
        new_user_id = auth_response.user.id
        
        # Cria o perfil do usuário na nossa tabela 'users'
        user_profile = models.User(id=new_user_id, email=user_data.email, name=user_data.name)
        db.add(user_profile)
        db.commit()
        
        print(f"Perfil de usuário criado com sucesso para ID: {new_user_id}")
        return {"message": "Usuário criado com sucesso! Verifique seu email para confirmação."}

    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login", summary="Autentica um usuário")
def auth_login(user_credentials: schemas.UserLogin):
    """
    Autentica um usuário com email e senha via Supabase Auth e retorna
    a sessão (incluindo o token JWT) se as credenciais forem válidas.
    """
    print(f"Recebida solicitação de login para: {user_credentials.email}")
    try:
        user_session = supabase_backend_client.auth.sign_in_with_password(
            {"email": user_credentials.email, "password": user_credentials.password}
        )
        return {"user": user_session.user.dict(), "session": user_session.session.dict()}
    except Exception as e:
        print(f"Falha no login para {user_credentials.email}: {e}")
        raise HTTPException(status_code=401, detail="Credenciais de login inválidas.")


# -----------------------------------------------------------------------------
# 4. Endpoints de Dados
# -----------------------------------------------------------------------------

@app.get("/users/{telefone}/transactions", response_model=List[schemas.Transaction], summary="Lista as transações de um usuário")
def get_user_transactions(telefone: str, db: Session = Depends(get_db)):
    """
    Busca todas as transações de um usuário, usando o número de telefone
    normalizado para encontrar o 'sender_id' correspondente.
    """
    telefone_limpo = ''.join(filter(str.isdigit, telefone))
    if not telefone_limpo.startswith('55'):
        telefone_limpo = f"55{telefone_limpo}"
    sender_id_formatado = f"whatsapp:+{telefone_limpo}"
    
    print(f"Buscando transações para o sender_id NORMALIZADO: {sender_id_formatado}")

    transacoes = db.query(models.Transaction)\
                   .filter(models.Transaction.sender_id == sender_id_formatado)\
                   .order_by(models.Transaction.created_at.desc())\
                   .all()

    if not transacoes:
        raise HTTPException(status_code=404, detail="Nenhuma transação encontrada para este usuário.")
        
    return transacoes

# -----------------------------------------------------------------------------
# 5. Webhook Principal (Twilio)
# -----------------------------------------------------------------------------

@app.post("/webhook/twilio", summary="Recebe mensagens do WhatsApp via Twilio")
async def webhook_twilio(request: Request, db: Session = Depends(get_db)):
    """
    Ponto de entrada para todas as mensagens do WhatsApp. Ele salva a mensagem,
    a enriquece com dados da IA e responde ao usuário.
    """
    try:
        form_data = await request.form()
        message_body = form_data.get("Body", "Mensagem vazia")
        sender_id = form_data.get("From", "Número desconhecido")

        print(f"MENSAGEM RECEBIDA de {sender_id}: {message_body}")

        # Busca o usuário na nossa tabela 'users' para obter o ID de autenticação.
        # Esta lógica precisará ser aprimorada para lidar com números não cadastrados.
        dono_da_transacao = db.query(models.User).filter(models.User.email.contains(sender_id.split(':')[-1][2:])).first() # Este é um HACK temporário

        # Persistência Inicial
        nova_transacao = models.Transaction(
            sender_id=sender_id,
            owner_id=dono_da_transacao.id if dono_da_transacao else None, # Usa o ID do usuário se encontrado
            message_body=message_body
        )
        db.add(nova_transacao)
        db.commit()
        db.refresh(nova_transacao)
        print(f"Transação bruta salva no DB com ID: {nova_transacao.id}")

        # Análise com IA
        dados_analisados = ia.analisar_transacao_simples(message_body)
        print(f"IA retornou dados estruturados: {dados_analisados}")

        # Enriquecimento dos Dados no Banco
        if dados_analisados and not dados_analisados.get("error"):
            nova_transacao.item = dados_analisados.get('item')
            nova_transacao.valor = dados_analisados.get('valor')
            nova_transacao.categoria = dados_analisados.get('categoria')
            db.commit()
            print(f"Transação ID {nova_transacao.id} enriquecida com dados da IA.")
        
        # Construção da Resposta para o WhatsApp
        twiml_response = MessagingResponse()
        if dados_analisados and not dados_analisados.get("error"):
            valor_recebido = dados_analisados.get('valor')
            valor_numerico = valor_recebido if valor_recebido is not None else 0.0
            item = dados_analisados.get('item', 'não identificado')
            categoria = dados_analisados.get('categoria', 'não identificada')
            resposta_formatada = (f"Entendido! ✅\n\nItem: *{item}*\nValor: *R$ {valor_numerico:.2f}*\nCategoria: *{categoria}*")
            twiml_response.message(resposta_formatada)
        else:
            twiml_response.message("Recebido! Salvei sua anotação, mas não consegui extrair os detalhes.")

        return Response(content=str(twiml_response), media_type="application/xml")

    except Exception as e:
        print(f"--- ERRO CRÍTICO NO WEBHOOK: {e} ---")
        db.rollback()
        error_response = MessagingResponse()
        error_response.message("Desculpe, ocorreu um erro inesperado ao processar sua mensagem.")
        return Response(content=str(error_response), media_type="application/xml")