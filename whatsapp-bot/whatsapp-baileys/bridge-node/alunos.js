const axios = require('axios');
const apiUrl = process.env.API_BASE_URL || process.env.API_URL || 'http://localhost:8000';
const API_BASE_URL = apiUrl.replace(/\/api\/chat\/?$/, '').replace(/\/$/, '');
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: Number(process.env.API_TIMEOUT || 15000),
});

function normalizar(valor) {
  return String(valor ?? '').trim().toLowerCase();
}

async function carregarAlunos(params = {}) {
  const resposta = await api.get('/alunos', { params });
  return Array.isArray(resposta.data) ? resposta.data : [];
}

function corresponde(valorAluno, valorComunicado) {
  if (valorComunicado === undefined || valorComunicado === null || valorComunicado === '') {
    return true;
  }
  return normalizar(valorAluno) === normalizar(valorComunicado);
}

function telefoneParaJid(telefone) {
  const identificador = String(telefone ?? '').trim();
  if (identificador.includes('@')) return identificador;
  const numero = identificador.replace(/\D/g, '');
  return numero ? `${numero}@s.whatsapp.net` : null;
}

async function listarAlunosDoComunicado(comunicado) {
  const curso = comunicado.curso ?? comunicado.curso_id;
  const semestre = comunicado.semestre ?? comunicado.semestre_id;

  // Sem os dois vínculos, o bot não faz disparo para evitar atingir alunos indevidos.
  if (curso === undefined || curso === null || semestre === undefined || semestre === null) {
    return [];
  }

  const alunos = await carregarAlunos({ curso, semestre });

  // O cadastro local pode ser trocado por uma chamada ao backend no futuro.
  return alunos
    .filter((aluno) => corresponde(aluno.curso, curso))
    .filter((aluno) => corresponde(aluno.semestre, semestre))
    .map((aluno) => telefoneParaJid(aluno.usuario_id))
    .filter(Boolean);
}

async function buscarAlunoPorJid(jid) {
  const numero = String(jid ?? '').split('@')[0];
  const alunos = await carregarAlunos();
  return alunos.find((aluno) => telefoneParaJid(aluno.usuario_id).split('@')[0].replace(/\D/g, '') === numero) || null;
}

module.exports = {
  listarAlunosDoComunicado,
  buscarAlunoPorJid,
};
