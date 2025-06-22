import os
import openai
from .database import SessionLocal
from .models import Evento
import asyncio # Importar para melhorias de performance

# --- Configuração Segura da API Key ---
# A chave NUNCA deve estar no código.
# Para desenvolver localmente, crie um arquivo chamado '.env' na raiz do projeto
# e adicione a linha: OPENAI_API_KEY='sk-sua-chave-aqui'
# Instale a biblioteca 'python-dotenv' (pip install python-dotenv) e use 'load_dotenv()'
# no início do seu app para carregar a variável.
openai.api_key = os.getenv("OPENAI_API_KEY")


async def consulta_ia(telefone: str, prompt: str) -> str:
    """
    Consulta a IA da OpenAI com o histórico do usuário para obter uma análise financeira.
    """
    # Busca o histórico do banco de dados de forma assíncrona para não travar o app
    historico = await get_historico_async(telefone)

    try:
        # Chama a API da OpenAI de forma assíncrona
        resposta = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Você é um assistente financeiro chamado RADAR. Seja objetivo, direto e visionário."},
                # É uma boa prática separar o histórico do prompt do usuário para a IA entender melhor
                {"role": "user", "content": f"Aqui está meu histórico recente de transações:\n{historico}\n\nCom base nisso, {prompt}"}
            ],
            temperature=0.7
        )
        # Extrai e retorna apenas o conteúdo da mensagem de resposta
        return resposta["choices"][0]["message"]["content"]
    except Exception as e:
        # Tratamento de erro básico caso a API da OpenAI falhe
        print(f"Erro ao consultar a API da OpenAI: {e}")
        return "Desculpe, não consegui consultar minha inteligência no momento. Tente novamente mais tarde."


def get_historico(telefone: str) -> str:
    """
    Busca o histórico de transações de um usuário no banco de dados.
    (Versão Síncrona - Bloqueia a execução)
    """
    # Usar 'with' garante que a sessão do banco de dados (db) será fechada automaticamente,
    # mesmo que ocorra um erro. Isso evita vazamento de recursos.
    with SessionLocal() as db:
        # A query busca os 5 eventos mais recentes do usuário
        eventos = db.query(Evento).filter(Evento.telefone == telefone).order_by(Evento.criado_em.desc()).limit(5).all()
        
        # Formata cada evento em uma linha de texto
        linhas = [f"{e.tipo.upper()}: {e.descricao} - R${e.valor or ''}" for e in eventos]
        
        # Junta as linhas em uma única string
        return "\n".join(linhas)

async def get_historico_async(telefone: str) -> str:
    """
    Wrapper assíncrono para a função síncrona get_historico.
    Executa a chamada ao banco de dados em uma thread separada para não bloquear o loop de eventos principal.
    """
    return await asyncio.to_thread(get_historico, telefone)