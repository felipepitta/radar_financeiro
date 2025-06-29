import os
import json
from openai import OpenAI

# Inicializa o cliente da OpenAI. 
# A chave é lida da variável de ambiente OPENAI_API_KEY, que é carregada no main.py
try:
    client = OpenAI()
except Exception as e:
    print(f"ERRO: Falha ao inicializar o cliente da OpenAI. Verifique sua chave de API. Erro: {e}")
    client = None

def analisar_transacao_simples(texto_mensagem: str) -> dict | None:
    """
    Usa a IA para extrair dados estruturados de uma única mensagem de texto.
    Esta função é para registrar novas transações (ex: "comprei pão 10 reais").
    """
    if not client:
        return {"error": "Cliente da OpenAI não inicializado."}

    print(f"IA (Análise Simples): Analisando o texto: '{texto_mensagem}'")
    try:
        # Usamos client.chat.completions.create, que é a sintaxe da versão nova da biblioteca
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"}, # Nova feature para garantir que a resposta seja JSON
            messages=[
                {
                    "role": "system",
                    "content": """Você é um assistente financeiro especialista em extrair dados de texto não estruturado.
                    Analise o texto do usuário e retorne um objeto JSON com as seguintes chaves: 'item' (string), 'valor' (float), e 'categoria' (string).
                    Categorias possíveis são: 'Receita', 'Alimentação', 'Transporte', 'Lazer', 'Moradia', 'Trabalho', 'Outros'.
                    Se não conseguir identificar algum campo, retorne null para ele. Responda APENAS com o objeto JSON válido."""
                },
                {
                    "role": "user",
                    "content": texto_mensagem
                }
            ]
        )
        resultado_json = response.choices[0].message.content
        print(f"IA (Análise Simples): Resposta bruta recebida: {resultado_json}")
        return json.loads(resultado_json)

    except Exception as e:
        print(f"IA (Análise Simples): Ocorreu um erro: {e}")
        return {"error": str(e)}

def gerar_analise_financeira(historico_transacoes_csv: str, pergunta_usuario: str) -> str:
    """
    Usa a IA para gerar uma análise com base no histórico de transações e uma pergunta do usuário.
    Esta é a função usada pela página de Recomendações do Dashboard.
    """
    if not client:
        return "Desculpe, meu cérebro de IA não está funcionando no momento."

    print(f"IA (Análise de Recomendações): Gerando insight para a pergunta: '{pergunta_usuario}'")
    
    # **MELHORIA 1: System Prompt mais detalhado, como no nosso blueprint.**
    system_prompt = (
        "Você é o 'Gem Radar', um assistente financeiro amigável e especialista para o app Radar Financeiro. "
        "Seu tom é prestativo e didático, como um mentor financeiro. Responda em Markdown para melhor formatação no chat. "
        "Analise os dados de transações do usuário, que estão em formato CSV, e responda à pergunta dele da forma mais útil e clara possível."
    )
    
    # **MELHORIA 2: Dados do usuário claramente formatados e separados da pergunta.**
    user_prompt_content = (
        f"**Aqui está o histórico de transações do usuário:**\n"
        f"```csv\n{historico_transacoes_csv}\n```\n\n"
        f"**Com base nesses dados, por favor, responda à seguinte pergunta:**\n"
        f"{pergunta_usuario}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt_content}
            ],
            temperature=0.4 # Um pouco menos criativo para manter as respostas mais factuais
        )
        print("IA (Análise de Recomendações): Resposta recebida da API.")
        return response.choices[0].message.content

    except Exception as e:
        print(f"IA (Análise de Recomendações): Ocorreu um erro ao chamar a API: {e}")
        return "Desculpe, não consegui consultar minha inteligência no momento. Tente novamente mais tarde."