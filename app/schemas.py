from pydantic import BaseModel

class WebhookIn(BaseModel):
    telefone: str
    mensagem: str