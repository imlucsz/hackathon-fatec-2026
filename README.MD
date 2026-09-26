# Fala Fatec

> Assistente de comunicação acadêmica da FATEC Itaquera, desenvolvido no 1º Hackathon FATEC Itaquera em 26/09/2026.

O Fala Fatec reúne uma API FastAPI, integração com Google Gemini e um bot de WhatsApp para facilitar o acesso dos alunos a avisos, aulas, provas, eventos e orientação por IA.

## Sobre o problema e a solução

### Problema

Informações acadêmicas importantes podem ficar espalhadas em diferentes canais, dificultando o acesso rápido dos alunos a mudanças de aula, datas de provas, comunicados e eventos.

### Solução

O MVP oferece um ponto de atendimento pelo WhatsApp. O aluno envia a primeira mensagem, escolhe uma opção no menu e recebe informações acadêmicas ou encaminha uma dúvida para o Gemini. Professores podem alimentar comunicados pela API, e o bridge pode distribuir avisos aos alunos vinculados ao curso e semestre.

O bot não inicia conversas comuns. A única exceção é o envio ativo de um comunicado oficial para os alunos correspondentes.

## Equipe

| Nome | Papel / função | GitHub / contato |
| :--- | :--- | :--- |
| Lucas | Tech Lead / Arquiteto / IA e suporte geral | A definir |
| Gael | Back-end Web e API Core (FastAPI) | A definir |
| Thiago | Back-end WhatsApp e automação | A definir |
| Cauê | Front-end Web e UI | A definir |
| A definir | Pitcher / Product Owner | A definir |
| A definir | UI/UX Designer / suporte Front | A definir |

## Stack tecnológica

- **API:** Python 3.11+ e FastAPI.
- **Documentação:** OpenAPI / Swagger em `/docs`.
- **IA:** Google AI Studio usando o SDK `google-genai` e o modelo configurado em `GEMINI_MODEL`.
- **WhatsApp:** Node.js, Baileys, QR Code e sessão local.
- **HTTP:** Axios no bridge Node.js.
- **Persistência do bridge:** JSON local para alunos e controle de comunicados enviados.
- **Versionamento:** Git e GitHub.

O MVP atual ainda não possui frontend, PostgreSQL ou autenticação de professores integrados. As rotas usam memória do processo e perdem os dados quando a API reinicia.

## Como rodar localmente

### Pré-requisitos

- Git.
- Python 3.11 ou superior.
- Node.js e npm.
- Uma chave do Google AI Studio.
- Um celular para vincular a sessão do WhatsApp.

### 1. Clonar e entrar no projeto

```bash
git clone https://github.com/imlucsz/hackathon-fatec-2026.git
cd hackathon-fatec-2026
```

### 2. Configurar o Python

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configurar o ambiente

Copie `.env.example` para `.env` e preencha a chave do Google AI Studio:

```env
GEMINI_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-3.8-flash
```

Nunca publique o arquivo `.env` ou uma chave de API. O arquivo está listado no `.gitignore`.

### 4. Iniciar a API

Na raiz do projeto, em um terminal:

```bash
venv/bin/uvicorn main:app --app-dir whatsapp-bot --reload --port 8000
```

No Windows, use `venv\Scripts\uvicorn.exe` no lugar de `venv/bin/uvicorn`.

- API: <http://localhost:8000>
- Swagger: <http://localhost:8000/docs>

### 5. Iniciar o bot WhatsApp

Em outro terminal:

```bash
cd whatsapp-bot/whatsapp-baileys
npm install
npm run bridge
```

Escaneie o QR Code pelo WhatsApp em **Configurações > Aparelhos conectados > Conectar um aparelho**.

O arquivo `alunos.json` deve conter os alunos vinculados:

```json
[
  {
    "telefone": "5511999999999",
    "curso": "ADS",
    "semestre": 1
  }
]
```

## Fluxo do bot

1. A primeira mensagem do aluno abre o menu.
2. `1` consulta as aulas de amanhã.
3. `2` consulta as próximas provas.
4. `3` consulta eventos internos.
5. `4` consulta eventos externos ainda válidos.
6. `5` registra uma sugestão de mudança.
7. `6` lista os últimos comunicados.
8. `7` encaminha a próxima mensagem para o Gemini.

O bridge consulta novos comunicados a cada 30 segundos. O controle por comunicado e destinatário fica em `comunicados-enviados.json` para evitar duplicidade.

## Contrato da API

### `POST /api/chat`

Request:

```json
{
  "mensagem": "Quais são minhas dúvidas sobre a prova?",
  "usuario_id": "5511999999999",
  "canal": "whatsapp",
  "curso": "ADS",
  "semestre": 1
}
```

Response:

```json
{
  "resposta": "Resposta gerada pelo Gemini.",
  "status": "sucesso"
}
```

### `POST /comunicados`

```json
{
  "titulo": "Alteração de sala",
  "conteudo": "A aula será na sala 12.",
  "curso": "ADS",
  "semestre": 1,
  "data": "2026-09-27"
}
```

### Consultas acadêmicas

```text
GET /comunicados?curso=ADS&semestre=1
GET /aulas/amanha?curso=ADS&semestre=1
GET /provas?curso=ADS&semestre=1
GET /eventos?tipo=interno
GET /eventos?tipo=externo
```

### `POST /sugestoes`

```json
{
  "mensagem": "Criar um calendário único para as turmas.",
  "usuario_id": "5511999999999",
  "curso": "ADS",
  "semestre": 1
}
```

## Transparência no uso de IA

O projeto utiliza o Google Gemini via Google AI Studio para:

- responder dúvidas gerais dos alunos;
- interpretar mensagens recebidas no modo IA;
- gerar orientações e sugestões relacionadas à experiência acadêmica.

A IA não deve inventar datas, provas, aulas ou comunicados. Informações oficiais são consultadas pelas rotas da API e pelos comunicados cadastrados.

## Gestão do projeto

O código e o histórico de desenvolvimento estão disponíveis no GitHub:

- Repositório público: <https://github.com/imlucsz/hackathon-fatec-2026>
- Board / Kanban: a definir pelo time

## Licença

Este projeto está sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE).