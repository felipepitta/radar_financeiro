import os
import openai
from .database import SessionLocal
from .models import Evento

openai.api_key = os.getenv("OPENAI_API_KEY")

async def consulta_ia(telefone: str, prompt: str) -> str:
    historico = get_historico(telefone)

    resposta = await openai.ChatCompletion.acreate(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Você é um assistente financeiro chamado RADAR. Seja objetivo, direto e visionário."},
            {"role": "user", "content": historico + "\nUsuário: " + prompt}
        ],
        temperature=0.7
    )
    return resposta["choices"][0]["message"]["content"]

def get_historico(telefone: str) -> str:
    db = SessionLocal()
    eventos = db.query(Evento).filter(Evento.telefone == telefone).order_by(Evento.criado_em.desc()).limit(5).all()
    linhas = [f"{e.tipo.upper()}: {e.descricao} - R${e.valor or ''}" for e in eventos]
    return "\n".join(linhas)