# Importa as ferramentas necessárias da biblioteca SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Define o "endereço" do banco de dados.
# "sqlite:///" indica que estamos usando o dialeto SQLite.
# "radar.db" é o nome do arquivo que será o nosso banco de dados.
# O comentário é uma excelente prática, lembrando de trocar para um banco mais robusto em produção.
DATABASE_URL = "sqlite:///radar.db"

# Cria o "motor" da aplicação, o ponto central de comunicação com o banco de dados.
# É configurado para usar o endereço que definimos acima.
# O argumento 'connect_args' é específico para SQLite e permite que a aplicação (que pode usar várias threads)
# se comunique com o banco sem erros.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Cria uma "fábrica" de sessões. Uma sessão é uma conversa individual com o banco.
# 'SessionLocal' não é uma sessão, mas uma classe que, quando chamada (ex: db = SessionLocal()), cria uma sessão.
# autocommit=False: As alterações precisam de um 'db.commit()' explícito para serem salvas.
# autoflush=False: Dá mais controle sobre quando as alterações são enviadas para o banco.
# bind=engine: Vincula esta fábrica de sessões ao motor que acabamos de criar.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cria uma classe base para todos os nossos modelos (tabelas).
# Qualquer classe que herdar de 'Base' será automaticamente reconhecida pelo SQLAlchemy como uma tabela.
Base = declarative_base()