# Importa a classe principal do Pydantic, que dá os poderes de validação.
from pydantic import BaseModel

# Define um "Schema" para validar os dados de entrada de um webhook.
# Um Schema é um contrato que os dados devem seguir para serem considerados válidos.
# A classe herda de 'BaseModel' para ganhar a capacidade de validar automaticamente.
class WebhookIn(BaseModel):
    # O campo 'telefone' é obrigatório e deve ser do tipo string.
    # Ex: "5511999999999"
    telefone: str
    
    # O campo 'mensagem' é obrigatório e deve ser do tipo string.
    # Ex: "Quero saber meu saldo"
    mensagem: str