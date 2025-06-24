# -----------------------------------------------------------------------------
# models.py - Definição das Tabelas do Banco de Dados
# -----------------------------------------------------------------------------
# Este arquivo contém os modelos do SQLAlchemy, que são representações em Python
# das tabelas do nosso banco de dados PostgreSQL. Cada classe aqui é uma tabela.
# -----------------------------------------------------------------------------

# 1. Imports: Agrupados por tipo para melhor legibilidade
# Bibliotecas padrão do Python
from datetime import datetime

# Bibliotecas de terceiros (SQLAlchemy)
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    DECIMAL, # Usado para precisão monetária
    func
)
from sqlalchemy.orm import relationship

# Imports da nossa aplicação
from .database import Base


# 2. Modelos de Tabela

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Relacionamento para o futuro
    transactions = relationship("Transaction", back_populates="owner")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    
    # CAMPO CRÍTICO: O número de telefone que enviou a mensagem (ex: whatsapp:+5511...)
    # Usamos este campo para buscar as transações no dashboard.
    sender_id = Column(String, index=True, nullable=False)
    
    message_body = Column(String, nullable=False)
    item = Column(String, nullable=True)
    categoria = Column(String, nullable=True)
    valor = Column(DECIMAL(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Chave estrangeira para o ID do usuário (opcional por enquanto)
    # No futuro, quando o webhook souber qual usuário está logado, preencheremos isso.
    owner_id = Column(String, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="transactions")