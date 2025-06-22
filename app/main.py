import uvicorn
from fastapi import FastAPI
from .database import SessionLocal, engine
from .models import Base, Evento
from .schemas import WebhookIn
from .ia import consulta_ia

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/webhook")
async def receber_mensagem(msg: WebhookIn):
    db = SessionLocal()
    texto = msg.mensagem.lower().strip()

    if texto.startswith("agenda:"):
        descricao = texto.replace("agenda:", "").strip()
        novo = Evento(telefone=msg.telefone, tipo="agenda", descricao=descricao)
    elif texto.startswith("gasto:"):
        partes = texto.replace("gasto:", "").strip().split()
        valor = float(partes[0])
        categoria = " ".join(partes[1:])
        novo = Evento(telefone=msg.telefone, tipo="gasto", descricao=categoria, valor=valor)
    else:
        resposta_ia = await consulta_ia(msg.telefone, texto)
        return {"resposta": resposta_ia}

    db.add(novo)
    db.commit()
    return {"resposta": f"Registrado com sucesso: {novo.tipo} - {novo.descricao}"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
