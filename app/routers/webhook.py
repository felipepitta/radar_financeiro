# ==============================================================================
# ARQUIVO: app/routers/webhook.py
# FUNÇÃO: Contém o endpoint que recebe as mensagens do WhatsApp via Twilio.
# ==============================================================================
from fastapi import APIRouter, Request, Response, Depends
from sqlalchemy.orm import Session
from twilio.twiml.messaging_response import MessagingResponse
from .. import models, ia
from ..database import get_db

def get_or_create_user_by_phone(db: Session, phone_number: str) -> models.User:
    """
    Busca um usuário pelo número de telefone. Se não encontrar, cria um novo.
    Retorna sempre uma instância de usuário válida e persistida no banco.
    """
    user = db.query(models.User).filter(models.User.phone == phone_number).first()
    
    if not user:
        print(f"INFO: Criando novo usuário para o telefone: {phone_number}")
        new_user = models.User(phone=phone_number) # Adicione outros campos se houver, ex: name
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
        
    return user

router = APIRouter(tags=["Webhook"])

@router.post("/webhook/twilio", summary="Recebe mensagens do WhatsApp")
async def webhook_twilio(request: Request, db: Session = Depends(get_db)):
    try:
        form_data = await request.form()
        message_body = form_data.get("Body", "Mensagem vazia")
        sender_id = form_data.get("From", "Número desconhecido") # ex: "whatsapp:+5511..."
        
        telefone_usuario = sender_id.replace("whatsapp:+", "")
        dono_da_transacao = db.query(models.User).filter(models.User.phone == telefone_usuario).first()

        if not dono_da_transacao:
            # Lógica para lidar com números não cadastrados (opcional)
            print(f"AVISO: Mensagem recebida de um número não cadastrado: {sender_id}")
            # Poderíamos criar um usuário "convidado" ou simplesmente ignorar.
            # Por enquanto, vamos salvar a transação sem um 'owner_id'.
            # Esta é uma decisão de negócio importante. Para o teste, vamos permitir.
            # Em um cenário real, provavelmente só aceitaríamos de usuários cadastrados.
            pass # Continua a execução

        # Persistência Inicial
        nova_transacao = models.Transaction(
            sender_id=sender_id,
            owner_id=dono_da_transacao.id if dono_da_transacao else "user_nao_cadastrado", # Ajuste temporário
            message_body=message_body
        )
        db.add(nova_transacao)
        db.commit()
        db.refresh(nova_transacao)

        # Análise com IA
        dados_analisados = ia.analisar_transacao_simples(message_body)

        # Enriquecimento dos Dados no Banco
        if dados_analisados and not dados_analisados.get("error"):
            nova_transacao.item = dados_analisados.get('item')
            nova_transacao.valor = dados_analisados.get('valor')
            nova_transacao.categoria = dados_analisados.get('categoria')
            db.commit()
        
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
        error_response.message("Desculpe, ocorreu um erro inesperado.")
        return Response(content=str(error_response), media_type="application/xml")