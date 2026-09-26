"""
Serviço de integração do WhatsApp (Thiago - Back-end WhatsApp & Automação).

Responsabilidades (conforme especificação 5W2H):
1. Conectar via QR Code diretamente ao celular dedicado da equipe.
2. Escutar mensagens recebidas no WhatsApp.
3. Rotear cada mensagem para o núcleo FastAPI/Gemini (api_client.py).
4. Responder ao usuário no WhatsApp com o texto gerado pela IA.

Rodar com:
    python whatsapp_bot.py

Na primeira execução vai aparecer um QR Code no terminal:
escaneie com o WhatsApp do celular dedicado
(Configurações > Aparelhos conectados > Conectar um aparelho).
"""

import os
from dotenv import load_dotenv

from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv, event
from neonize.utils.message import extract_text

from api_client import perguntar_ia

load_dotenv()

SESSION_NAME = os.getenv("WA_SESSION_NAME", "hackathon-bot")
DB_PATH = os.getenv("WA_DB_PATH", "./whatsapp_session.db")

client = NewClient(name=SESSION_NAME, database=DB_PATH)


@client.event(ConnectedEv)
def on_connected(client: NewClient, ev: ConnectedEv):
    print("✅ Conectado ao WhatsApp! Bot pronto para receber mensagens.")


@client.event(MessageEv)
def on_message(client: NewClient, ev: MessageEv):
    # Ignora mensagens enviadas pelo próprio bot (eco)
    if getattr(ev.Info.MessageSource, "IsFromMe", False):
        return

    texto = extract_text(ev.Message)
    remetente = str(ev.Info.MessageSource.Sender)
    chat = ev.Info.MessageSource.Chat

    print(f"📨 [{remetente}] {texto}")

    # Roteia para o núcleo FastAPI/Gemini seguindo o contrato JSON padrão
    resposta = perguntar_ia(mensagem=texto, usuario_id=remetente)

    client.send_message(chat, text=resposta)
    print(f"📤 Resposta enviada para {remetente}")


if __name__ == "__main__":
    print("📱 Escaneie o QR Code abaixo com o celular dedicado do bot:")
    client.connect()
    event.wait()
