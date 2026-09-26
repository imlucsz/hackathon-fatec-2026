from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String
from sqlalchemy.sql import func

from database import Base

class Comunicado(Base):
    __tablename__ = "comunicados"

    id = Column(Integer, primary_key=True, index=True)
    mensagem = Column(String, nullable=False)
    curso = Column(String, nullable=False, default="todos")
    semestre = Column(Integer, nullable=True)
    categoria = Column(String, nullable=False, default="aviso_geral")
    enviado = Column(Boolean, default=False, nullable=False)
    link = Column(String, nullable=True)
    data_expiracao = Column(DateTime(timezone=True), nullable=True)
    data_publicacao = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ComunicadoBase(BaseModel):
    mensagem: str
    curso: str = "todos"
    semestre: Optional[int] = None
    categoria: Literal["aula", "prova", "evento_interno", "evento_externo", "aviso_geral"] = "aviso_geral"
    enviado: bool = False
    link: Optional[str] = None
    data_expiracao: Optional[datetime] = None

class ComunicadoAtualizar(BaseModel):
    mensagem: Optional[str] = None
    curso: Optional[str] = None
    semestre: Optional[int] = None
    categoria: Optional[Literal["aula", "prova", "evento_interno", "evento_externo", "aviso_geral"]] = None
    enviado: Optional[bool] = None
    link: Optional[str] = None
    data_expiracao: Optional[datetime] = None

class ComunicadoResposta(ComunicadoBase):
    id: int
    data_publicacao: datetime

    model_config = ConfigDict(from_attributes=True)

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

class TokenResposta(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ProfessorResposta(BaseModel):
    id: int
    ra: str
    email: str
    disciplina: str

    model_config = ConfigDict(from_attributes=True)

class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(String, unique=True, index=True, nullable=False)
    curso = Column(String, nullable=False)
    semestre = Column(Integer, nullable=False)

class AlunoCriar(BaseModel):
    usuario_id: str
    curso: str
    semestre: int

class AlunoResposta(BaseModel):
    id: int
    usuario_id: str
    curso: str
    semestre: int

    model_config = ConfigDict(from_attributes=True)

class Aula(Base):
    __tablename__ = "aulas"

    id = Column(Integer, primary_key=True, index=True)
    disciplina = Column(String, nullable=False)
    professor = Column(String, nullable=True)
    data = Column(Date, nullable=False, index=True)
    horario = Column(String, nullable=True)
    sala = Column(String, nullable=True)
    curso = Column(String, nullable=False, index=True)
    semestre = Column(Integer, nullable=False, index=True)

class AulaCriar(BaseModel):
    disciplina: str
    professor: Optional[str] = None
    data: date
    horario: Optional[str] = None
    sala: Optional[str] = None
    curso: str
    semestre: int

class AulaResposta(AulaCriar):
    id: int

    model_config = ConfigDict(from_attributes=True)

class Prova(Base):
    __tablename__ = "provas"

    id = Column(Integer, primary_key=True, index=True)
    disciplina = Column(String, nullable=False)
    data = Column(Date, nullable=False, index=True)
    horario = Column(String, nullable=True)
    sala = Column(String, nullable=True)
    curso = Column(String, nullable=False, index=True)
    semestre = Column(Integer, nullable=False, index=True)

class ProvaCriar(BaseModel):
    disciplina: str
    data: date
    horario: Optional[str] = None
    sala: Optional[str] = None
    curso: str
    semestre: int

class ProvaResposta(ProvaCriar):
    id: int

    model_config = ConfigDict(from_attributes=True)

class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descricao = Column(String, nullable=False)
    data = Column(Date, nullable=False, index=True)
    horario = Column(String, nullable=True)
    local = Column(String, nullable=True)
    tipo = Column(String, nullable=False, index=True)
    link = Column(String, nullable=True)
    data_expiracao = Column(Date, nullable=True)
    curso = Column(String, nullable=True, index=True)
    semestre = Column(Integer, nullable=True, index=True)

class EventoCriar(BaseModel):
    titulo: str
    descricao: str
    data: date
    horario: Optional[str] = None
    local: Optional[str] = None
    tipo: Literal["interno", "externo"]
    link: Optional[str] = None
    data_expiracao: Optional[date] = None
    curso: Optional[str] = None
    semestre: Optional[int] = None

class EventoResposta(EventoCriar):
    id: int

    model_config = ConfigDict(from_attributes=True)

class Sugestao(Base):
    __tablename__ = "sugestoes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(String, nullable=False)
    curso = Column(String, nullable=False)
    mensagem = Column(String, nullable=False)
    data_envio = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class SugestaoCriar(BaseModel):
    usuario_id: str
    curso: Optional[str] = None
    mensagem: str

class SugestaoResposta(SugestaoCriar):
    id: int
    data_envio: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    mensagem: str
    usuario_id: str
    canal: str = "whatsapp"

class ChatResposta(BaseModel):
    resposta: str
    status: str

class ErrorResponse(BaseModel):
    detail: str
    status_code: int = 400