import os
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import schemas_models as sm
from database import get_db

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)
JWT_SECRET = os.getenv("JWT_SECRET", "fatec-itaquera-secret")
JWT_ALGORITHM = "HS256"

def gerar_hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha_plana, senha_hash)

def criar_token_professor(ra: str) -> str:
    payload = {
        "sub": ra,
        "exp": datetime.now(timezone.utc) + timedelta(hours=8),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def obter_professor_atual(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> sm.Professor:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de autenticação ausente")

    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        ra = payload.get("sub")
        if not ra:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado") from exc

    professor = db.query(sm.Professor).filter(sm.Professor.ra == ra).first()
    if not professor:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Professor não encontrado")

    return professor

router = APIRouter()

@router.post("/professores", response_model=sm.ProfessorResposta, status_code=status.HTTP_201_CREATED)
def criar_professor(professor: sm.ProfessorCriar, db: Session = Depends(get_db)):
    try:
        senha_criptografada = gerar_hash_senha(professor.senha)
        novo_professor = sm.Professor(
            ra=professor.ra,
            email=professor.email,
            disciplina=professor.disciplina,
            senha=senha_criptografada,
        )
        db.add(novo_professor)
        db.commit()
        db.refresh(novo_professor)
        return novo_professor
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Professor já cadastrado com esses dados")

@router.post("/login", response_model=sm.TokenResposta)
def login_professor(credenciais: sm.ProfessorLogin, db: Session = Depends(get_db)):
    professor = db.query(sm.Professor).filter(sm.Professor.ra == credenciais.ra).first()

    if not professor or not verificar_senha(credenciais.senha, professor.senha):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="RA ou senha incorretos")

    token = criar_token_professor(professor.ra)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/comunicados", response_model=sm.ComunicadoResposta, status_code=status.HTTP_201_CREATED)
def criar_comunicado(
    comunicado: sm.ComunicadoBase,
    db: Session = Depends(get_db),
    professor: sm.Professor = Depends(obter_professor_atual),
):
    del professor
    dados = comunicado.model_dump(exclude_none=True)
    curso = str(dados.get("curso") or "todos").strip().lower()
    dados["curso"] = curso

    if dados.get("categoria") is None:
        dados["categoria"] = "aviso_geral"

    novo_comunicado = sm.Comunicado(**dados)
    db.add(novo_comunicado)
    db.commit()
    db.refresh(novo_comunicado)
    return novo_comunicado

@router.get("/comunicados", response_model=list[sm.ComunicadoResposta])
def listar_comunicados(
    db: Session = Depends(get_db),
    curso: Optional[str] = Query(default=None, description="Curso ou 'todos' para geral"),
    semestre: Optional[int] = Query(default=None, description="Semestre do comunicado"),
    categoria: Optional[str] = Query(default=None, description="Categoria do comunicado"),
):
    query = db.query(sm.Comunicado)

    if curso is not None:
        curso_normalizado = curso.strip().lower()
        if curso_normalizado != "todos":
            query = query.filter(sm.Comunicado.curso == curso_normalizado)
        else:
            query = query.filter(sm.Comunicado.curso == "todos")

    if semestre is not None:
        query = query.filter(sm.Comunicado.semestre == semestre)

    if categoria is not None:
        query = query.filter(sm.Comunicado.categoria == categoria)

    return query.order_by(sm.Comunicado.data_publicacao.desc()).all()

@router.get("/comunicados/pendentes", response_model=list[sm.ComunicadoResposta])
def listar_pendentes(db: Session = Depends(get_db)):
    return (
        db.query(sm.Comunicado)
        .filter(sm.Comunicado.enviado.is_(False))
        .order_by(sm.Comunicado.data_publicacao.asc())
        .all()
    )

@router.get("/comunicados/{comunicado_id}", response_model=sm.ComunicadoResposta)
def buscar_comunicado(comunicado_id: int, db: Session = Depends(get_db)):
    comunicado = db.query(sm.Comunicado).filter(sm.Comunicado.id == comunicado_id).first()
    if not comunicado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comunicado não encontrado")
    return comunicado

@router.patch("/comunicados/{comunicado_id}/marcar-enviado")
def marcar_como_enviado(
    comunicado_id: int,
    payload: Optional[sm.ComunicadoAtualizar] = None,
    db: Session = Depends(get_db),
    professor: sm.Professor = Depends(obter_professor_atual),
):
    del professor
    comunicado = db.query(sm.Comunicado).filter(sm.Comunicado.id == comunicado_id).first()
    if not comunicado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comunicado não encontrado")

    if payload is not None and payload.enviado is not None:
        comunicado.enviado = payload.enviado
    else:
        comunicado.enviado = True

    db.commit()
    db.refresh(comunicado)
    return {
        "status": "sucesso",
        "mensagem": "Comunicado marcado como enviado" if comunicado.enviado else "Comunicado reaberto",
        "enviado": comunicado.enviado,
    }

@router.put("/comunicados/{comunicado_id}", response_model=sm.ComunicadoResposta)
def atualizar_comunicado(
    comunicado_id: int,
    dados: sm.ComunicadoAtualizar,
    db: Session = Depends(get_db),
    professor: sm.Professor = Depends(obter_professor_atual),
):
    del professor
    comunicado = db.query(sm.Comunicado).filter(sm.Comunicado.id == comunicado_id).first()
    if not comunicado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comunicado não encontrado")

    campos = dados.model_dump(exclude_unset=True)
    if "curso" in campos and campos["curso"] is not None:
        campos["curso"] = str(campos["curso"]).strip().lower()

    for campo, valor in campos.items():
        setattr(comunicado, campo, valor)

    db.commit()
    db.refresh(comunicado)
    return comunicado

@router.delete("/comunicados/{comunicado_id}")
def deletar_comunicado(
    comunicado_id: int,
    db: Session = Depends(get_db),
    professor: sm.Professor = Depends(obter_professor_atual),
):
    del professor
    comunicado = db.query(sm.Comunicado).filter(sm.Comunicado.id == comunicado_id).first()
    if not comunicado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comunicado não encontrado")

    db.delete(comunicado)
    db.commit()
    return {"status": "sucesso", "mensagem": "Comunicado removido com sucesso"}

@router.post("/alunos", response_model=sm.AlunoResposta, status_code=status.HTTP_201_CREATED)
def criar_aluno(aluno: sm.AlunoCriar, db: Session = Depends(get_db)):
    try:
        novo_aluno = sm.Aluno(
            usuario_id=aluno.usuario_id,
            curso=str(aluno.curso).strip().lower(),
            semestre=aluno.semestre,
        )
        db.add(novo_aluno)
        db.commit()
        db.refresh(novo_aluno)
        return novo_aluno
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Aluno já cadastrado")

@router.get("/alunos", response_model=list[sm.AlunoResposta])
def listar_alunos(
    db: Session = Depends(get_db),
    curso: Optional[str] = Query(default=None, description="Filtrar por curso"),
    semestre: Optional[int] = Query(default=None, description="Filtrar por semestre"),
):
    query = db.query(sm.Aluno)

    if curso is not None:
        query = query.filter(sm.Aluno.curso == str(curso).strip().lower())

    if semestre is not None:
        query = query.filter(sm.Aluno.semestre == semestre)

    return query.order_by(sm.Aluno.id.asc()).all()

def filtrar_por_aluno(query, modelo, curso: Optional[str], semestre: Optional[int]):
    if curso:
        query = query.filter(modelo.curso == curso.strip().lower())
    if semestre is not None:
        query = query.filter(modelo.semestre == semestre)
    return query

@router.get("/aulas/amanha", response_model=list[sm.AulaResposta])
def listar_aulas_amanha(
    db: Session = Depends(get_db),
    curso: Optional[str] = Query(default=None),
    semestre: Optional[int] = Query(default=None),
):
    amanha = date.today() + timedelta(days=1)
    query = db.query(sm.Aula).filter(sm.Aula.data == amanha)
    query = filtrar_por_aluno(query, sm.Aula, curso, semestre)
    return query.order_by(sm.Aula.horario.asc()).all()

@router.post("/aulas", response_model=sm.AulaResposta, status_code=status.HTTP_201_CREATED)
def criar_aula(
    aula: sm.AulaCriar,
    db: Session = Depends(get_db),
    professor: sm.Professor = Depends(obter_professor_atual),
):
    del professor
    dados = aula.model_dump()
    dados["curso"] = dados["curso"].strip().lower()
    nova_aula = sm.Aula(**dados)
    db.add(nova_aula)
    db.commit()
    db.refresh(nova_aula)
    return nova_aula

@router.get("/provas", response_model=list[sm.ProvaResposta])
def listar_provas(
    db: Session = Depends(get_db),
    curso: Optional[str] = Query(default=None),
    semestre: Optional[int] = Query(default=None),
):
    query = db.query(sm.Prova).filter(sm.Prova.data >= date.today())
    query = filtrar_por_aluno(query, sm.Prova, curso, semestre)
    return query.order_by(sm.Prova.data.asc(), sm.Prova.horario.asc()).all()

@router.post("/provas", response_model=sm.ProvaResposta, status_code=status.HTTP_201_CREATED)
def criar_prova(
    prova: sm.ProvaCriar,
    db: Session = Depends(get_db),
    professor: sm.Professor = Depends(obter_professor_atual),
):
    del professor
    dados = prova.model_dump()
    dados["curso"] = dados["curso"].strip().lower()
    nova_prova = sm.Prova(**dados)
    db.add(nova_prova)
    db.commit()
    db.refresh(nova_prova)
    return nova_prova

@router.get("/eventos", response_model=list[sm.EventoResposta])
def listar_eventos(
    db: Session = Depends(get_db),
    tipo: Optional[str] = Query(default=None, pattern="^(interno|externo)$"),
    curso: Optional[str] = Query(default=None),
    semestre: Optional[int] = Query(default=None),
):
    query = db.query(sm.Evento).filter(
        sm.Evento.data >= date.today(),
        (sm.Evento.data_expiracao.is_(None) | (sm.Evento.data_expiracao >= date.today())),
    )
    if tipo:
        query = query.filter(sm.Evento.tipo == tipo)
    query = filtrar_por_aluno(query, sm.Evento, curso, semestre)
    return query.order_by(sm.Evento.data.asc()).all()

@router.post("/eventos", response_model=sm.EventoResposta, status_code=status.HTTP_201_CREATED)
def criar_evento(
    evento: sm.EventoCriar,
    db: Session = Depends(get_db),
    professor: sm.Professor = Depends(obter_professor_atual),
):
    del professor
    dados = evento.model_dump()
    if dados["curso"]:
        dados["curso"] = dados["curso"].strip().lower()
    novo_evento = sm.Evento(**dados)
    db.add(novo_evento)
    db.commit()
    db.refresh(novo_evento)
    return novo_evento

@router.post("/api/chat", response_model=sm.ChatResposta)
def chat_ia(payload: sm.ChatRequest):
    mensagem = payload.mensagem.strip()
    if not mensagem:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mensagem não pode estar vazia")

    try:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            resposta = (
                "Olá! O assistente de IA está configurado, mas a chave de API do Gemini não foi definida "
                "no ambiente. Configure GEMINI_API_KEY para ativar a resposta completa."
            )
            return {"resposta": resposta, "status": "sucesso"}

        try:
            from google import genai

            client = genai.Client(api_key=api_key)
            resposta_model = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=mensagem,
            )
            resposta = getattr(resposta_model, "text", str(resposta_model))
            return {"resposta": resposta, "status": "sucesso"}
        except Exception:
            resposta = (
                "Recebi sua mensagem e encaminhei para o módulo de IA, mas a resposta do Gemini não pôde "
                "ser completada no momento. Tente novamente em instantes."
            )
            return {"resposta": resposta, "status": "erro"}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao processar a mensagem: {str(exc)}") from exc

@router.post("/sugestoes", response_model=sm.SugestaoResposta, status_code=status.HTTP_201_CREATED)
def criar_sugestao(sugestao: sm.SugestaoCriar, db: Session = Depends(get_db)):
    nova_sugestao = sm.Sugestao(
        usuario_id=sugestao.usuario_id,
        curso=(sugestao.curso or "todos").strip().lower(),
        mensagem=sugestao.mensagem,
    )
    db.add(nova_sugestao)
    db.commit()
    db.refresh(nova_sugestao)
    return nova_sugestao

@router.get("/health")
def healthcheck():
    return {"status": "ok"}