# ==============================================================================
# ARQUIVO: app/dependencies.py
# FUNÇÃO: Centraliza a criação de clientes de serviços externos.
# ==============================================================================
from supabase import create_client, Client
from .config import settings

# Cliente do Supabase para operações de backend (usando a chave de serviço secreta)
supabase_backend_client: Client = create_client(
    settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY
)