const fs = require('fs/promises');
const path = require('path');

const arquivoAlunos = process.env.ALUNOS_FILE || path.join(__dirname, '..', 'alunos.json');

function normalizar(valor) {
  return String(valor ?? '').trim().toLowerCase();
}

async function carregarAlunos() {
  try {
    const conteudo = await fs.readFile(arquivoAlunos, 'utf8');
    const alunos = JSON.parse(conteudo);
    return Array.isArray(alunos) ? alunos : [];
  } catch (erro) {
    if (erro.code !== 'ENOENT') {
      console.error('[alunos] Não foi possível ler o cadastro local:', erro.message);
    }
    return [];
  }
}

function corresponde(valorAluno, valorComunicado) {
  if (valorComunicado === undefined || valorComunicado === null || valorComunicado === '') {
    return true;
  }
  return normalizar(valorAluno) === normalizar(valorComunicado);
}

function telefoneParaJid(telefone) {
  const numero = String(telefone ?? '').replace(/\D/g, '');
  return numero ? `${numero}@s.whatsapp.net` : null;
}

async function listarAlunosDoComunicado(comunicado) {
  const alunos = await carregarAlunos();
  const curso = comunicado.curso ?? comunicado.curso_id;
  const semestre = comunicado.semestre ?? comunicado.semestre_id;

  // Sem os dois vínculos, o bot não faz disparo para evitar atingir alunos indevidos.
  if (curso === undefined || curso === null || semestre === undefined || semestre === null) {
    return [];
  }

  // O cadastro local pode ser trocado por uma chamada ao backend no futuro.
  return alunos
    .filter((aluno) => corresponde(aluno.curso ?? aluno.curso_id, curso))
    .filter((aluno) => corresponde(aluno.semestre ?? aluno.semestre_id, semestre))
    .map((aluno) => telefoneParaJid(aluno.telefone ?? aluno.whatsapp ?? aluno.numero))
    .filter(Boolean);
}

async function buscarAlunoPorJid(jid) {
  const numero = String(jid ?? '').split('@')[0];
  const alunos = await carregarAlunos();
  return alunos.find((aluno) => String(aluno.telefone ?? aluno.whatsapp ?? aluno.numero).replace(/\D/g, '') === numero) || null;
}

module.exports = {
  listarAlunosDoComunicado,
  buscarAlunoPorJid,
};
