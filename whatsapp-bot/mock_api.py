"""
Testes rápidos da mock_api.py (contrato /api/chat), em Python puro.

Uso:
    1) suba o mock em outro terminal -> uvicorn mock_api:app --reload --port 8000
    2) rode este script -> python test_mock_api.py
"""

from fastapi import Fastapi
from pydantic import BaseModel
import json
import time
import requests

BASE_URL = "http://localhost:8000/api/chat"
app = FastAPI(title="Mock API - Hackathon FATEC (stub de teste)")

def print_titulo(texto: str):
    print("\n" + "=" * 50)
    print(texto)
    print("=" * 50)


def print_resposta(resp: requests.Response):
    print(f"Status HTTP: {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except ValueError:
        print(f"Corpo (não é JSON): {resp.text}")


def teste_1_mensagem_valida():
    print_titulo("1) Mensagem válida (fluxo feliz)")
    payload = {
        "mensagem": "Oi, tudo bem?",
        "usuario_id": "5511999999999",
        "canal": "whatsapp",
    }
    resp = requests.post(BASE_URL, json=payload, timeout=10)
    print_resposta(resp)


def teste_2_canal_diferente():
    print_titulo("2) Canal diferente (site) - deve aceitar normalmente")
    payload = {"mensagem": "teste pelo site", "usuario_id": "123", "canal": "site"}
    resp = requests.post(BASE_URL, json=payload, timeout=10)
    print_resposta(resp)


def teste_3_campo_faltando():
    print_titulo("3) Campo obrigatório faltando (usuario_id e canal) - espera 422")
    payload = {"mensagem": "teste sem usuario_id"}
    resp = requests.post(BASE_URL, json=payload, timeout=10)
    print_resposta(resp)


def teste_4_mensagem_vazia():
    print_titulo("4) Mensagem vazia - ver como a API lida")
    payload = {"mensagem": "", "usuario_id": "123", "canal": "whatsapp"}
    resp = requests.post(BASE_URL, json=payload, timeout=10)
    print_resposta(resp)


def teste_5_json_malformado():
    print_titulo("5) JSON malformado (corpo cru, não serializado) - espera erro")
    # Manda um corpo que não é JSON válido de propósito
    resp = requests.post(
        BASE_URL,
        data="{mensagem: 'sem aspas'}",  # corpo bruto, não json=...
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    print_resposta(resp)


def teste_6_latencia():
    print_titulo("6) Medição de latência (mock simula 0.5s de delay)")
    payload = {"mensagem": "teste de latencia", "usuario_id": "123", "canal": "whatsapp"}
    inicio = time.time()
    resp = requests.post(BASE_URL, json=payload, timeout=10)
    duracao = time.time() - inicio
    print(f"Status HTTP: {resp.status_code}")
    print(f"Tempo total: {duracao:.3f}s")


def teste_7_timeout_simulado():
    print_titulo("7) Timeout simulado (timeout=0.001s, deve estourar)")
    payload = {"mensagem": "teste timeout", "usuario_id": "123", "canal": "whatsapp"}
    try:
        requests.post(BASE_URL, json=payload, timeout=0.001)
        print("Não estourou timeout (inesperado nessa rede)")
    except requests.exceptions.Timeout:
        print("Timeout capturado corretamente ✅ (é assim que o api_client.py deve reagir)")


def teste_8_api_fora_do_ar():
    print_titulo("8) API fora do ar (porta errada) - simula servidor indisponível")
    url_errada = "http://localhost:9999/api/chat"
    payload = {"mensagem": "teste", "usuario_id": "123", "canal": "whatsapp"}
    try:
        requests.post(url_errada, json=payload, timeout=3)
        print("Não deu erro de conexão (inesperado)")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão capturado corretamente ✅: {type(e).__name__}")


if __name__ == "__main__":
    teste_1_mensagem_valida()
    teste_2_canal_diferente()
    teste_3_campo_faltando()
    teste_4_mensagem_vazia()
    teste_5_json_malformado()
    teste_6_latencia()
    teste_7_timeout_simulado()
    teste_8_api_fora_do_ar()

    print_titulo("Testes concluídos. Doc interativa em: http://localhost:8000/docs")