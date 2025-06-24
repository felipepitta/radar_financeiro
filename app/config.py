from pydantic_settings import BaseSettings, SettingsConfigDict

# Esta classe herda de BaseSettings e automaticamente lê as variáveis
# de um arquivo .env ou do ambiente do sistema.
class Settings(BaseSettings):
    # Defina aqui TODAS as suas variáveis de ambiente com seus tipos.
    # O Pydantic irá validar se elas existem no .env ao iniciar.
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str 
    SUPABASE_SERVICE_KEY: str
    OPENAI_API_KEY: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str

    # Configura o Pydantic para ler do arquivo chamado '.env' na raiz do projeto
    model_config = SettingsConfigDict(env_file=".env")

# Cria uma instância única das configurações que será importada
# pelo resto da nossa aplicação.
settings = Settings()