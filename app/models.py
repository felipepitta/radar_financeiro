# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    transactions = relationship("Transaction", back_populates="owner")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(String, index=True, nullable=False)
    message_body = Column(String, nullable=False)
    item = Column(String, nullable=True)
    categoria = Column(String, nullable=True)
    valor = Column(DECIMAL(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="transactions")