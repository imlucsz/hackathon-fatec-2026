# Hackathon FATEC Itaquera 2026

Solução full-stack integrada (Site Web + Bot de WhatsApp) impulsionada por LLM (Google Gemini), desenvolvida durante o Hackathon da FATEC Itaquera em 26/09/2026.

## Equipe

| Nome | Papel |
|---|---|
| Lucas | Tech Lead / Arquiteto / IA & Suporte Geral |
| Gael | Back-end Web & API Core (FastAPI) |
| Thiago | Back-end WhatsApp & Automação |
| Cauê | Front-end Web & UI |
| _(a definir)_ | Pitcher / Product Owner |
| _(a definir)_ | UI/UX Designer / Suporte Front |

## Stack Tecnológica

- **Back-end:** Python 3.11+ com FastAPI
- **Documentação de API:** OpenAPI / Swagger (`/docs`)
- **IA / LLM:** Google AI Studio (Gemini 2.5 Flash)
- **Integração WhatsApp:** Webhook / QR Code
- **Banco de dados local atual:** SQLite (`backend/banco.db`)
- **Front-end:** HTML5, CSS3 (Tailwind via CDN), JavaScript
- **Versionamento:** Git / GitHub

## Sobre o problema

_(a preencher após a revelação do tema)_

## Como rodar localmente

O frontend ainda não está implementado. Para testar a API e o bot, use dois terminais PowerShell na raiz do repositório.

### 1. Instalar dependências Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Configure `GEMINI_API_KEY` no arquivo `.env` da raiz para habilitar respostas reais do Gemini. Sem a chave, as rotas da API continuam disponíveis, mas a IA não responde usando o modelo.

### 2. Iniciar o backend

No primeiro terminal:

```powershell
.\.venv\Scripts\Activate.ps1
Set-Location backend
python -m uvicorn main:app --reload --env-file ..\.env --host 127.0.0.1 --port 8000
```

A API cria as tabelas SQLite automaticamente. Health check: `http://127.0.0.1:8000/health`. Documentação interativa: `http://127.0.0.1:8000/docs`.

### 3. Iniciar o bot de WhatsApp

No segundo terminal, a partir da raiz do repositório:

```powershell
Set-Location whatsapp-bot\whatsapp-baileys
npm.cmd ci
npm.cmd run bridge
```

Na primeira execução, escaneie o QR code em **WhatsApp > Configurações > Aparelhos conectados**. Mantenha os dois terminais abertos. Para testar o menu, envie uma mensagem, responda `7` e depois envie sua pergunta.

Cadastre alunos em `POST /alunos` usando o número de WhatsApp (somente dígitos) como `usuario_id`. Aulas, provas e eventos devem ser cadastrados pela API; as rotas de gravação exigem login de professor. O bot consulta essas informações no SQLite pela API.

## Contrato de dados

**Request** `POST /api/chat`
```json
{
  "mensagem": "texto do usuário",
  "usuario_id": "string",
  "canal": "site|whatsapp"
}
```

**Response**
```json
{
  "resposta": "texto gerado pela IA",
  "status": "sucesso|erro"
}
```