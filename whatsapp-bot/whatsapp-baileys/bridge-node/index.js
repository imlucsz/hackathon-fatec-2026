const path = require('path');

require('dotenv').config({
  path: process.env.DOTENV_CONFIG_PATH || path.join(__dirname, '..', '.env'),
});

const axios = require('axios');
const {
  DisconnectReason,
  makeWASocket,
  useMultiFileAuthState,
} = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const qrcode = require('qrcode-terminal');
const { foiEnviado, marcarComoEnviado } = require('./armazenamento');
const { listarAlunosDoComunicado, buscarAlunoPorJid } = require('./alunos');

const urlConfigurada = process.env.API_BASE_URL || process.env.API_URL || 'http://localhost:8000';
const API_BASE_URL = urlConfigurada.replace(/\/api\/chat\/?$/, '').replace(/\/$/, '');
const API_CHAT_PATH = process.env.API_CHAT_PATH || '/api/chat';
const API_TIMEOUT = Number(process.env.API_TIMEOUT || 15000);
const POLLING_MS = Number(process.env.COMUNICADOS_POLLING_MS || 30000);
const AUTH_FOLDER = process.env.WA_AUTH_FOLDER || './auth_info';
const MENU = [
  '1. Aula de amanhã',
  '2. Datas das provas',
  '3. Eventos internos',
  '4. Eventos externos',
  '5. Enviar sugestão de mudança',
  '6. Ver últimos avisos',
  '7. Falar com a IA (dúvidas gerais)',
].join('\n');
const estadosDosAlunos = new Map();
let pollingAtivo = false;
let pollingTimer;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
});

function extrairMensagemTexto(mensagem) {
  const conteudo = mensagem.message || {};
  return (
    conteudo.conversation ||
    conteudo.extendedTextMessage?.text ||
    conteudo.imageMessage?.caption ||
    conteudo.videoMessage?.caption ||
    ''
  ).trim();
}

function idDoComunicado(comunicado) {
  return String(comunicado.id ?? comunicado.comunicado_id ?? comunicado.uuid ?? '');
}

function formatarComunicado(comunicado) {
  const titulo = comunicado.titulo ?? comunicado.title ?? 'Novo comunicado';
  const conteudo = comunicado.conteudo ?? comunicado.conteúdo ?? comunicado.mensagem ?? comunicado.descricao ?? '';
  return `![📢](https://discord.com/assets/7401aa22d4169631.svg) [Aviso da FATEC] ${titulo}\n\n${conteudo}`;
}

function dataDoComunicado(comunicado) {
  return new Date(comunicado.created_at ?? comunicado.data_criacao ?? comunicado.data ?? 0).getTime() || 0;
}

function estaNoCursoDoAluno(comunicado, aluno) {
  if (!aluno) return true;
  const cursoComunicado = comunicado.curso ?? comunicado.curso_id;
  const semestreComunicado = comunicado.semestre ?? comunicado.semestre_id;
  const normalizar = (valor) => String(valor ?? '').trim().toLowerCase();

  return (!cursoComunicado || normalizar(cursoComunicado) === normalizar(aluno.curso ?? aluno.curso_id)) &&
    (!semestreComunicado || normalizar(semestreComunicado) === normalizar(aluno.semestre ?? aluno.semestre_id));
}

async function buscarComunicados() {
  const resposta = await api.get('/comunicados');
  return Array.isArray(resposta.data) ? resposta.data : resposta.data.comunicados || [];
}

async function enviarNovosComunicados(sock) {
  let comunicados;
  try {
    comunicados = await buscarComunicados();
  } catch (erro) {
    console.error('[comunicados] API indisponível; novo ciclo tentará novamente:', erro.message);
    return;
  }

  // O estado é salvo por comunicado e destinatário para permitir novas tentativas.
  for (const comunicado of comunicados.sort((a, b) => dataDoComunicado(a) - dataDoComunicado(b))) {
    const comunicadoId = idDoComunicado(comunicado);
    if (!comunicadoId) {
      console.warn('[comunicados] Comunicado ignorado porque não possui ID.');
      continue;
    }

    const destinatarios = await listarAlunosDoComunicado(comunicado);
    if (!destinatarios.length) {
      console.warn(`[comunicados] Nenhum aluno vinculado ao comunicado ${comunicadoId}.`);
      continue;
    }

    for (const destinatario of destinatarios) {
      if (await foiEnviado(comunicadoId, destinatario)) continue;

      try {
        await sock.sendMessage(destinatario, { text: formatarComunicado(comunicado) });
        await marcarComoEnviado(comunicadoId, destinatario);
        console.log(`[comunicados] Comunicado ${comunicadoId} enviado para ${destinatario}.`);
      } catch (erro) {
        console.error(`[comunicados] Falha ao enviar para ${destinatario}:`, erro.message);
      }
    }
  }
}

async function iniciarPolling(sock) {
  if (pollingAtivo) return;
  pollingAtivo = true;
  await enviarNovosComunicados(sock);
  pollingTimer = setInterval(() => enviarNovosComunicados(sock).catch((erro) => {
    console.error('[comunicados] Erro inesperado no ciclo:', erro.message);
  }), POLLING_MS);
}

function pararPolling() {
  if (pollingTimer) clearInterval(pollingTimer);
  pollingTimer = undefined;
  pollingAtivo = false;
}

async function enviarMenu(sock, jid) {
  await sock.sendMessage(jid, {
    text: `Olá! Sou o Fala Fatec. Escolha uma opção respondendo com o número:\n\n${MENU}`,
  });
}

async function enviarUltimosAvisos(sock, jid) {
  try {
    const aluno = await buscarAlunoPorJid(jid);
    const comunicados = (await buscarComunicados())
      .filter((comunicado) => estaNoCursoDoAluno(comunicado, aluno))
      .sort((a, b) => dataDoComunicado(b) - dataDoComunicado(a))
      .slice(0, 5);

    if (!comunicados.length) {
      await sock.sendMessage(jid, { text: 'Não encontrei avisos recentes para o seu curso e semestre.' });
      return;
    }

    await sock.sendMessage(jid, {
      text: comunicados.map(formatarComunicado).join('\n\n--------------------\n\n'),
    });
  } catch (erro) {
    console.error('[menu] Não foi possível consultar os avisos:', erro.message);
    await sock.sendMessage(jid, { text: 'Não consegui consultar os avisos agora. Tente novamente em instantes.' });
  }
}

async function buscarAlunoEConsultar(jid, rota, parametros = {}) {
  const aluno = await buscarAlunoPorJid(jid);
  const resposta = await api.get(rota, {
    params: {
      curso: aluno?.curso,
      semestre: aluno?.semestre,
      ...parametros,
    },
  });
  return resposta.data;
}

function formatarAgenda(item) {
  const detalhes = [item.data, item.horario, item.sala || item.local].filter(Boolean).join(' | ');
  return `• ${item.disciplina || item.titulo}\n${detalhes}${item.descricao ? `\n${item.descricao}` : ''}${item.link ? `\nLink: ${item.link}` : ''}`;
}

async function enviarAulasDeAmanha(sock, jid) {
  try {
    const itens = await buscarAlunoEConsultar(jid, '/aulas/amanha');
    await sock.sendMessage(jid, { text: itens.length ? `📚 Aulas de amanhã:\n\n${itens.map(formatarAgenda).join('\n\n')}` : 'Não encontrei aulas cadastradas para amanhã.' });
  } catch (erro) {
    console.error('[menu] Falha ao consultar aulas:', erro.message);
    await sock.sendMessage(jid, { text: 'Não consegui consultar as aulas agora. Tente novamente em instantes.' });
  }
}

async function enviarProvas(sock, jid) {
  try {
    const itens = await buscarAlunoEConsultar(jid, '/provas');
    await sock.sendMessage(jid, { text: itens.length ? `📝 Próximas provas:\n\n${itens.map(formatarAgenda).join('\n\n')}` : 'Não encontrei próximas provas cadastradas.' });
  } catch (erro) {
    console.error('[menu] Falha ao consultar provas:', erro.message);
    await sock.sendMessage(jid, { text: 'Não consegui consultar as provas agora. Tente novamente em instantes.' });
  }
}

async function enviarEventos(sock, jid, tipo, titulo) {
  try {
    const itens = await buscarAlunoEConsultar(jid, '/eventos', { tipo });
    await sock.sendMessage(jid, { text: itens.length ? `${titulo}:\n\n${itens.map(formatarAgenda).join('\n\n')}` : `Não encontrei ${tipo === 'interno' ? 'eventos internos' : 'eventos externos'} próximos.` });
  } catch (erro) {
    console.error(`[menu] Falha ao consultar eventos ${tipo}:`, erro.message);
    await sock.sendMessage(jid, { text: 'Não consegui consultar os eventos agora. Tente novamente em instantes.' });
  }
}

async function solicitarSugestao(sock, jid, texto) {
  try {
    const aluno = await buscarAlunoPorJid(jid);
    await api.post('/sugestoes', {
      mensagem: texto,
      usuario_id: jid.split('@')[0],
      curso: aluno?.curso,
      semestre: aluno?.semestre,
    });
    await sock.sendMessage(jid, { text: 'Sugestão recebida. Obrigado por ajudar a melhorar a FATEC!' });
  } catch (erro) {
    console.error('[sugestoes] Falha ao registrar sugestão:', erro.message);
    await sock.sendMessage(jid, { text: 'Não consegui registrar sua sugestão agora. Tente novamente em instantes.' });
  }
}

async function encaminharParaIa(sock, jid, texto) {
  try {
    const aluno = await buscarAlunoPorJid(jid);
    const resposta = await api.post(API_CHAT_PATH, {
      mensagem: texto,
      usuario_id: jid.split('@')[0],
      canal: 'whatsapp',
      curso: aluno?.curso,
      semestre: aluno?.semestre,
    });
    const textoResposta = resposta.data?.resposta || 'Não consegui gerar uma resposta agora.';
    await sock.sendMessage(jid, { text: textoResposta });
  } catch (erro) {
    console.error('[ia] Falha ao chamar /api/chat:', erro.message);
    await sock.sendMessage(jid, { text: 'A IA está indisponível no momento. Tente novamente em instantes.' });
  }
}

async function tratarMensagem(sock, mensagem) {
  if (mensagem.key.fromMe || !mensagem.message) return;
  const jid = mensagem.key.remoteJid;
  if (!jid || jid.endsWith('@g.us') || jid === 'status@broadcast') return;

  const texto = extrairMensagemTexto(mensagem);
  if (!texto) return;

  const comando = texto.toLowerCase();
  const estado = estadosDosAlunos.get(jid);

  // A primeira mensagem apenas abre o menu; o bot não inicia contato sozinho.
  if (comando === 'menu' || !estado) {
    estadosDosAlunos.set(jid, 'menu');
    await enviarMenu(sock, jid);
    return;
  }

  if (estado === 'ia') {
    estadosDosAlunos.set(jid, 'menu');
    await encaminharParaIa(sock, jid, texto);
    return;
  }

  if (estado === 'sugestao') {
    estadosDosAlunos.set(jid, 'menu');
    await solicitarSugestao(sock, jid, texto);
    return;
  }

  if (texto === '1') {
    await enviarAulasDeAmanha(sock, jid);
    return;
  }

  if (texto === '2') {
    await enviarProvas(sock, jid);
    return;
  }

  if (texto === '3') {
    await enviarEventos(sock, jid, 'interno', '🏫 Eventos internos');
    return;
  }

  if (texto === '4') {
    await enviarEventos(sock, jid, 'externo', '🌐 Eventos externos');
    return;
  }

  if (texto === '5') {
    estadosDosAlunos.set(jid, 'sugestao');
    await sock.sendMessage(jid, { text: 'Digite sua sugestão de mudança na próxima mensagem.' });
    return;
  }

  if (texto === '6') {
    await enviarUltimosAvisos(sock, jid);
    return;
  }

  if (texto === '7') {
    estadosDosAlunos.set(jid, 'ia');
    await sock.sendMessage(jid, { text: 'Envie sua dúvida ou sugestão para a IA na próxima mensagem.' });
    return;
  }

  await enviarMenu(sock, jid);
}

async function iniciarBot() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_FOLDER);
  const sock = makeWASocket({ auth: state });

  sock.ev.on('creds.update', saveCreds);
  sock.ev.on('messages.upsert', ({ messages }) => {
    for (const mensagem of messages) {
      tratarMensagem(sock, mensagem).catch((erro) => console.error('[mensagens] Erro ao processar:', erro.message));
    }
  });
  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect, qr } = update;
    if (qr) {
      console.log('📱 Escaneie o QR Code abaixo:');
      qrcode.generate(qr, { small: true });
    }
    if (connection === 'open') {
      console.log('✅ Conectado ao WhatsApp.');
      iniciarPolling(sock).catch((erro) => console.error('[comunicados] Falha ao iniciar polling:', erro.message));
    }
    if (connection === 'close') {
      pararPolling();
      const statusCode = new Boom(lastDisconnect?.error)?.output?.statusCode;
      const deveReconectar = statusCode !== DisconnectReason.loggedOut;
      console.error('[whatsapp] Conexão fechada:', { statusCode, deveReconectar });
      if (deveReconectar) iniciarBot().catch((erro) => console.error('[whatsapp] Falha ao reconectar:', erro.message));
    }
  });
}

iniciarBot().catch((erro) => console.error('❌ Erro fatal ao iniciar o bot:', erro));
