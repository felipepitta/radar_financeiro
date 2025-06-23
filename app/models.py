# Importa todas as ferramentas necessárias do SQLAlchemy e do Python
from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    DateTime, 
    ForeignKey, 
    Numeric,
    func
)
from sqlalchemy.orm import relationship
from datetime import datetime

# Importa a classe Base, que é a fundação para os modelos
from .database import Base


class Usuario(Base):
    """
    Define o modelo para a tabela de 'usuarios'.
    Cada instância desta classe representa uma linha na tabela 'usuarios'.
    """
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    telefone = Column(String, unique=True, index=True)
    
    # RELACIONAMENTO: Um usuário pode ter múltiplos eventos.
    # Acessível via 'meu_usuario.eventos'.
    # 'back_populates' cria a ligação de volta a partir do modelo Evento.
    eventos = relationship("Evento", back_populates="usuario", cascade="all, delete-orphan")


class Evento(Base):
    """
    Define o modelo para a tabela de 'eventos' (transações financeiras).
    Cada instância representa uma linha na tabela 'eventos'.
    """
    __tablename__ = "eventos"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String)
    descricao = Column(String)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Usar Numeric para precisão financeira é a melhor prática.
    valor = Column(Numeric(10, 2), nullable=True)
    
    # CHAVE ESTRANGEIRA (FOREIGN KEY): Liga este evento a um usuário.
    # "usuarios.id" aponta para a tabela 'usuarios' e a coluna 'id'.
    # O banco de dados agora garante que este 'usuario_id' deve existir na tabela de usuários.
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    
    # RELACIONAMENTO: Um evento pertence a um único usuário.
    # Acessível via 'meu_evento.usuario'.
    # 'back_populates' cria a ligação de volta a partir do modelo Usuario.
    usuario = relationship("Usuario", back_populates="eventos")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(String, nullable=False)
    message_body = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())