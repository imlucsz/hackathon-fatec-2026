from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import schemas_models as sm
from database import get_db

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def gerar_hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha_plana, senha_hash)

router = APIRouter()

# Cadastro de professor
@router.post("/professores", response_model=sm.ProfessorResposta)
def criar_professor(professor: sm.ProfessorCriar, db: Session = Depends(get_db)):
    senha_criptografada = gerar_hash_senha(professor.senha)
    
    novo_professor = sm.Professor(
        ra=professor.ra,
        email=professor.email,
        disciplina=professor.disciplina,
        senha=senha_criptografada
    )
    
    db.add(novo_professor)
    db.commit()
    db.refresh(novo_professor)
    return novo_professor

# Login de professor
@router.post("/login", response_model=sm.ProfessorResposta)
def login_professor(credenciais: sm.ProfessorLogin, db: Session = Depends(get_db)):
    professor = db.query(sm.Professor).filter(sm.Professor.ra == credenciais.ra).first()
    
    if not professor or not verificar_senha(credenciais.senha, professor.senha):
        raise HTTPException(status_code=401, detail="RA ou senha incorretos")
    
    return professor

# Criar novo comunicado
@router.post("/comunicados", response_model=sm.ComunicadoResposta)
def criar_comunicado(comunicado: sm.ComunicadoBase, db: Session = Depends(get_db)):
    novo_comunicado = sm.Comunicado(**comunicado.model_dump()) 
    db.add(novo_comunicado)
    db.commit()
    db.refresh(novo_comunicado)
    return novo_comunicado

# Ler todos os comunicados
@router.get("/comunicados", response_model=list[sm.ComunicadoResposta])
def listar_comunicados(db: Session = Depends(get_db)):
    return db.query(sm.Comunicado).all()

# Ler um comunicado específico pelo ID
@router.get("/comunicados/{comunicado_id}", response_model=sm.ComunicadoResposta)
def buscar_comunicado(comunicado_id: int, db: Session = Depends(get_db)):
    comunicado = db.query(sm.Comunicado).filter(sm.Comunicado.id == comunicado_id).first()
    if not comunicado:
        raise HTTPException(status_code=404, detail="Comunicado não encontrado")
    return comunicado