from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    telefone = Column(String, unique=True, index=True)

class Evento(Base):
    __tablename__ = "eventos"
    id = Column(Integer, primary_key=True, index=True)
    telefone = Column(String, index=True)
    tipo = Column(String)
    descricao = Column(String)
    valor = Column(Float, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)