import os
from datetime import date, datetime
from itertools import count

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from google import genai

load_dotenv()

app = FastAPI()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
cliente_gemini = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

_ids = count(1)
comunicados: list[dict] = []
aulas: list[dict] = []
provas: list[dict] = []
eventos: list[dict] = []
sugestoes: list[dict] = []

# Modelos para validação do Contrato Único de Dados
class RequestPayload(BaseModel):
    mensagem: str
    usuario_id: str
    canal: str
    curso: str | None = None
    semestre: int | str | None = None

class ResponsePayload(BaseModel):
    resposta: str
    status: str

class ComunicadoPayload(BaseModel):
    titulo: str
    conteudo: str
    curso: str
    semestre: int | str
    data: str | None = None

class AulaPayload(BaseModel):
    disciplina: str
    professor: str | None = None
    data: str
    horario: str | None = None
    sala: str | None = None
    curso: str
    semestre: int | str

class ProvaPayload(BaseModel):
    disciplina: str
    data: str
    horario: str | None = None
    sala: str | None = None
    curso: str
    semestre: int | str

class EventoPayload(BaseModel):
    titulo: str
    descricao: str
    data: str
    horario: str | None = None
    local: str | None = None
    tipo: str = Field(pattern="^(interno|externo)$")
    link: str | None = None
    data_expiracao: str | None = None
    curso: str | None = None
    semestre: int | str | None = None

class SugestaoPayload(BaseModel):
    mensagem: str
    usuario_id: str
    curso: str | None = None
    semestre: int | str | None = None

def pertence_ao_aluno(item: dict, curso: str | None, semestre: str | int | None) -> bool:
    mesmo_curso = not curso or str(item.get("curso", "")).lower() == str(curso).lower()
    mesmo_semestre = not semestre or str(item.get("semestre", "")) == str(semestre)
    return mesmo_curso and mesmo_semestre

def futuros(items: list[dict]) -> list[dict]:
    hoje = date.today().isoformat()
    return [item for item in items if item.get("data", "") >= hoje]

@app.post("/api/chat", response_model=ResponsePayload)
def mock_chat(payload: RequestPayload):
    mensagem = payload.mensagem.strip()
    if not mensagem:
        return ResponsePayload(
            resposta="A mensagem enviada está vazia.",
            status="erro"
        )

    if cliente_gemini is None:
        return ResponsePayload(
            resposta="A IA ainda não foi configurada. Adicione GEMINI_API_KEY ao arquivo .env.",
            status="erro"
        )

    contexto_aluno = ""
    if payload.curso or payload.semestre:
        contexto_aluno = f"Contexto acadêmico: curso={payload.curso or 'não informado'}, semestre={payload.semestre or 'não informado'}."

    prompt = f"""
Você é o assistente Fala Fatec, da FATEC Itaquera.
Responda em português do Brasil, com clareza e objetividade.
Ajude com dúvidas acadêmicas, comunicação institucional e sugestões de melhoria para a FATEC.
Não invente datas, provas, aulas ou comunicados. Quando não souber, diga que a informação precisa ser confirmada pela instituição.
{contexto_aluno}

Mensagem do aluno:
{mensagem}
""".strip()

    try:
        resposta = cliente_gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        texto = (resposta.text or "").strip()
        if not texto:
            raise RuntimeError("O Gemini retornou uma resposta vazia")
        return ResponsePayload(resposta=texto, status="sucesso")
    except Exception as erro:
        print(f"[gemini] Erro ao gerar resposta: {erro}")
        return ResponsePayload(
            resposta="Não consegui consultar a IA agora. Tente novamente em instantes.",
            status="erro"
        )

@app.get("/comunicados")
def listar_comunicados(
    curso: str | None = None,
    semestre: str | None = None,
):
    return [item for item in comunicados if pertence_ao_aluno(item, curso, semestre)]

@app.post("/comunicados", status_code=201)
def criar_comunicado(payload: ComunicadoPayload):
    comunicado = {"id": next(_ids), **payload.model_dump(), "created_at": datetime.now().isoformat()}
    comunicados.append(comunicado)
    return comunicado

@app.get("/comunicados/{comunicado_id}")
def buscar_comunicado(comunicado_id: int):
    for comunicado in comunicados:
        if comunicado["id"] == comunicado_id:
            return comunicado
    raise HTTPException(status_code=404, detail="Comunicado não encontrado")

@app.get("/aulas/amanha")
def listar_aulas_amanha(curso: str | None = None, semestre: str | None = None):
    amanha = (date.today()).fromordinal(date.today().toordinal() + 1).isoformat()
    return [item for item in aulas if item["data"] == amanha and pertence_ao_aluno(item, curso, semestre)]

@app.post("/aulas", status_code=201)
def criar_aula(payload: AulaPayload):
    aula = {"id": next(_ids), **payload.model_dump()}
    aulas.append(aula)
    return aula

@app.get("/provas")
def listar_provas(curso: str | None = None, semestre: str | None = None):
    return [item for item in futuros(provas) if pertence_ao_aluno(item, curso, semestre)]

@app.post("/provas", status_code=201)
def criar_prova(payload: ProvaPayload):
    prova = {"id": next(_ids), **payload.model_dump()}
    provas.append(prova)
    return prova

@app.get("/eventos")
def listar_eventos(
    tipo: str | None = Query(default=None, pattern="^(interno|externo)$"),
):
    hoje = date.today().isoformat()
    return [item for item in futuros(eventos) if (not tipo or item["tipo"] == tipo) and
            (not item.get("data_expiracao") or item["data_expiracao"] >= hoje)]

@app.post("/eventos", status_code=201)
def criar_evento(payload: EventoPayload):
    evento = {"id": next(_ids), **payload.model_dump()}
    eventos.append(evento)
    return evento

@app.post("/sugestoes", status_code=201)
def criar_sugestao(payload: SugestaoPayload):
    sugestao = {"id": next(_ids), **payload.model_dump(), "criada_em": datetime.now().isoformat()}
    sugestoes.append(sugestao)
    return {"status": "recebida", "id": sugestao["id"]}
