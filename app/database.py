import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Carrega as variáveis de ambiente do arquivo .env para o sistema
load_dotenv()

# Pega a URL do banco de dados do ambiente, e não mais do código
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# O resto do arquivo continua igual...
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()