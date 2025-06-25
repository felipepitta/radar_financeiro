# ==============================================================================
# ARQUIVO: app/config.py
# FUNÇÃO: Carrega e valida TODAS as variáveis de ambiente de forma centralizada.
#         Este é o "cofre" seguro da nossa aplicação.
# ==============================================================================
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Define e carrega as configurações da aplicação a partir de um arquivo .env.
    O Pydantic garante que todas as variáveis declaradas aqui existam.
    """
    # Conexão com o banco de dados (usando o Connection Pooler)
    DATABASE_URL: str
    
    # Credenciais da API do Supabase - Apenas as necessárias para o backend
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str # Chave secreta para operações de backend
    
    # Credencial da OpenAI
    OPENAI_API_KEY: str

    # Configura o Pydantic para ler do arquivo chamado '.env' na raiz do projeto
    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

# Cria uma instância única das configurações que será usada em toda a aplicação.
settings = Settings()