"""
Camada de integração com o núcleo Back-end (Gael / FastAPI).

Segue ESTRITAMENTE o contrato definido na especificação 5W2H:

Request:
{
  "mensagem": "...",
  "usuario_id": "...",
  "canal": "site|whatsapp"
}

Response:
{
  "resposta": "...",
  "status": "sucesso|erro"
}
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000/api/chat")
TIMEOUT = float(os.getenv("API_TIMEOUT", "15"))


def perguntar_ia(mensagem: str, usuario_id: str) -> str:
    """
    Envia a mensagem do usuário do WhatsApp para o núcleo FastAPI/Gemini
    e devolve o texto de resposta pronto para reenviar no WhatsApp.

    Nunca lança exceção: em qualquer falha (timeout, API fora do ar,
    resposta inválida), devolve uma mensagem amigável — conforme a
    regra de negócio "Gestão de Exceções / Resiliência" do documento.
    """
    # Regra: mensagens vazias não podem quebrar o fluxo
    if not mensagem or not mensagem.strip():
        return "Desculpa, não entendi sua mensagem. Pode reescrever? 🙂"

    payload = {
        "mensagem": mensagem.strip(),
        "usuario_id": usuario_id,
        "canal": "whatsapp",
    }

    try:
        resp = requests.post(API_URL, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") == "sucesso" and data.get("resposta"):
            return data["resposta"]

        print(f"[api_client] Resposta com status inesperado: {data}")
        return "Tive um probleminha para processar sua pergunta agora. Tenta de novo em instantes? 🙏"

    except requests.exceptions.Timeout:
        print(f"[api_client] Timeout ao chamar {API_URL}")
        return "Estou demorando mais que o esperado pra responder. Tenta de novo em alguns segundos ⏳"

    except requests.exceptions.RequestException as e:
        print(f"[api_client] Erro de conexão com a API: {e}")
        return "No momento não consigo acessar meu 'cérebro' (a API central está indisponível). Já avisamos a equipe! 🤖⚠️"

    except ValueError:
        print("[api_client] A API retornou um corpo que não é JSON válido")
        return "Recebi uma resposta inesperada do servidor. Pode tentar novamente? 🔄"
