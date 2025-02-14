from database import Base
from sqlalchemy import Column, Integer, String, Float

class Produto(Base):
    __tablename__ = 'produtos'

    id = Column(Integer, primary_key=True)
    codigo = Column(Integer, unique=True, nullable=False)
    descricao = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    unidade = Column(String, nullable=False)