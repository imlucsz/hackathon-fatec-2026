require('dotenv').config();
const {
  makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
} = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const qrcode = require('qrcode-terminal');

const AUTH_FOLDER = process.env.WA_AUTH_FOLDER || './auth_info';

async function startBot() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_FOLDER);

  const sock = makeWASocket({
    auth: state,
  });

  sock.ev.on('creds.update', saveCreds);

  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      console.log('📱 Escaneie o QR Code abaixo com o celular dedicado:');
      console.log('   WhatsApp > Configurações > Aparelhos conectados > Conectar um aparelho');
      qrcode.generate(qr, { small: true });
    }

    if (connection === 'close') {
      const statusCode = new Boom(lastDisconnect?.error)?.output?.statusCode;
      const deveReconectar = statusCode !== DisconnectReason.loggedOut;

      console.log('🔌 Conexão fechada.', { statusCode, deveReconectar });

      if (deveReconectar) {
        console.log('🔁 Tentando reconectar...');
        startBot();
      } else {
        console.log('🚪 Sessão deslogada. Apague a pasta auth_info e escaneie o QR de novo.');
      }
    } else if (connection === 'open') {
      console.log('✅ Conectado ao WhatsApp! Bot pronto (ainda sem responder mensagens).');
    }
  });
}

startBot().catch((err) => {
  console.error('❌ Erro fatal ao iniciar o bot:', err);
});
