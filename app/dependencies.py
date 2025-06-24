# app/dependencies.py
import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase_backend_client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)