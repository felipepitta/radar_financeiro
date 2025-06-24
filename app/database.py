# ==============================================================================
# ARQUIVO: app/database.py
# FUNÇÃO: Configura a conexão com o banco de dados PostgreSQL usando SQLAlchemy.
# ==============================================================================
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings  # Importa a configuração central

# Cria o "motor" de conexão usando a URL validada pelo 'settings'.
engine = create_engine(settings.DATABASE_URL)

# Cria uma "fábrica" de sessões para conversar com o banco.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cria uma classe Base para que nossos modelos de tabela possam herdar dela.
Base = declarative_base()

# Função de Dependência para o FastAPI: garante que cada requisição tenha sua
# própria sessão de banco de dados e que ela seja fechada ao final.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()