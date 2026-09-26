from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Modelos para validação do Contrato Único de Dados
class RequestPayload(BaseModel):
    mensagem: str
    usuario_id: str
    canal: str

class ResponsePayload(BaseModel):
    resposta: str
    status: str

@app.post("/api/chat", response_model=ResponsePayload)
def mock_chat(payload: RequestPayload):
    # Tratamento simples para mensagem vazia conforme a regra do projeto
    if not payload.mensagem.strip():
        return ResponsePayload(
            resposta="A mensagem enviada está vazia.",
            status="erro"
        )
    
    # Resposta simulada reproduzindo o retorno do servidor
    return ResponsePayload(
        resposta=f"Simulação Gemini: Recebido '{payload.mensagem}' do usuário {payload.usuario_id} via {payload.canal}.",
        status="sucesso"
    )
