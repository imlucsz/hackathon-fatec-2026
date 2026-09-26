from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from pydantic import BaseModel
from database import Base
from datetime import datetime

class Comunicado(Base):
    __tablename__ = "comunicados"

    id = Column(Integer, primary_key=True, index=True)
    mensagem = Column(String, nullable=False)
    data_publicacao = Column(DateTime(timezone=True), server_default=func.now())

class ComunicadoBase(BaseModel):
    mensagem: str

class ComunicadoResposta(ComunicadoBase):
    id: int
    data_publicacao: datetime

    class Config:
        from_attributes = True

class Professor(Base):
    __tablename__ = "professores"

    id = Column(Integer, primary_key=True, index=True)
    ra = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    disciplina = Column(String, nullable=False)
    senha = Column(String, nullable=False)

class ProfessorCriar(BaseModel):
    ra: str
    email: str
    disciplina: str
    senha: str

class ProfessorLogin(BaseModel):
    ra: str
    senha: str

class ProfessorResposta(BaseModel):
    id: int
    ra: str
    email: str
    disciplina: str

    class Config:
        from_attributes = True