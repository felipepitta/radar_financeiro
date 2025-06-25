# ==============================================================================
# ARQUIVO: app/models.py
# FUNÇÃO: Define a estrutura das nossas tabelas no banco de dados.
# ==============================================================================
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    """Representa a tabela 'users'."""
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True) 
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    transactions = relationship("Transaction", back_populates="owner", cascade="all, delete-orphan")

class Transaction(Base):
    """Representa a tabela 'transactions'."""
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(String, index=True, nullable=False) # Armazena o 'whatsapp:+55...'
    message_body = Column(String, nullable=False)
    item = Column(String, nullable=True)
    categoria = Column(String, nullable=True)
    valor = Column(DECIMAL(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="transactions")