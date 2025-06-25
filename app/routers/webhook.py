# ==============================================================================
# ARQUIVO: app/routers/webhook.py
# FUNÇÃO: Contém o endpoint que recebe as mensagens do WhatsApp via Twilio.
# ==============================================================================
from fastapi import APIRouter, Request, Response, Depends, status # Adicione 'status'
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
        new_user = models.User(phone=phone_number)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
        
    return user

router = APIRouter(tags=["Webhook"])

@router.post("/webhook/twilio", summary="Recebe e processa mensagens do WhatsApp")
async def webhook_twilio(request: Request, db: Session = Depends(get_db)):
    try:
        form_data = await request.form()
        message_body = form_data.get("Body", "Mensagem vazia")
        sender_id = form_data.get("From", "Número desconhecido")
        
        # --- LÓGICA DE USUÁRIO ROBUSTA ---
        # AQUI ESTÁ A MUDANÇA: Usamos nossa nova função!
        telefone_usuario = sender_id.replace("whatsapp:+", "")
        dono_da_transacao = get_or_create_user_by_phone(db=db, phone_number=telefone_usuario)

        # --- PERSISTÊNCIA INICIAL ---
        # Agora, owner_id sempre será um ID válido.
        nova_transacao = models.Transaction(
            sender_id=sender_id,
            owner_id=dono_da_transacao.id, # ✅ Problema resolvido!
            message_body=message_body
        )
        db.add(nova_transacao)
        db.commit()
        db.refresh(nova_transacao)

        # --- ANÁLISE COM IA (sem alterações) ---
        dados_analisados = ia.analisar_transacao_simples(message_body)

        # --- ENRIQUECIMENTO DOS DADOS (sem alterações) ---
        if dados_analisados and not dados_analisados.get("error"):
            nova_transacao.item = dados_analisados.get('item')
            nova_transacao.valor = dados_analisados.get('valor')
            nova_transacao.categoria = dados_analisados.get('categoria')
            db.commit()
        
        # --- RESPOSTA PARA O WHATSAPP (sem alterações) ---
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
        if db.is_active:
            db.rollback()
        
        error_response = MessagingResponse()
        error_response.message("Desculpe, ocorreu um erro inesperado ao processar sua mensagem. Nossa equipe já foi notificada.")
        
        # ✅ Retornamos um erro 500 para sinalizar ao Twilio que algo falhou do nosso lado.
        return Response(
            content=str(error_response),
            media_type="application/xml",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )