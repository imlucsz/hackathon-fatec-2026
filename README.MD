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
- **Banco de dados:** PostgreSQL (Supabase / Neon)
- **Front-end:** HTML5, CSS3 (Tailwind via CDN), JavaScript
- **Versionamento:** Git / GitHub

## Sobre o problema

_(a preencher após a revelação do tema)_

## Como rodar localmente

_(a preencher)_

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