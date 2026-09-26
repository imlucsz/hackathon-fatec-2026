const fs = require('fs/promises');
const path = require('path');

const arquivoPadrao = path.join(__dirname, '..', 'comunicados-enviados.json');

async function lerEstado(caminho = arquivoPadrao) {
  try {
    const conteudo = await fs.readFile(caminho, 'utf8');
    const estado = JSON.parse(conteudo);
    return estado && typeof estado === 'object' ? estado : {};
  } catch (erro) {
    if (erro.code !== 'ENOENT') {
      console.error('[armazenamento] Não foi possível ler o estado:', erro.message);
    }
    return {};
  }
}

async function salvarEstado(estado, caminho = arquivoPadrao) {
  // A escrita temporária evita deixar o JSON incompleto se o processo for interrompido.
  await fs.mkdir(path.dirname(caminho), { recursive: true });
  const temporario = `${caminho}.tmp`;
  await fs.writeFile(temporario, `${JSON.stringify(estado, null, 2)}\n`, 'utf8');
  await fs.rename(temporario, caminho);
}

async function foiEnviado(comunicadoId, destinatario, caminho = arquivoPadrao) {
  const estado = await lerEstado(caminho);
  return Array.isArray(estado[comunicadoId]) && estado[comunicadoId].includes(destinatario);
}

async function marcarComoEnviado(comunicadoId, destinatario, caminho = arquivoPadrao) {
  const estado = await lerEstado(caminho);
  const destinatarios = new Set(Array.isArray(estado[comunicadoId]) ? estado[comunicadoId] : []);
  destinatarios.add(destinatario);
  estado[comunicadoId] = [...destinatarios];
  await salvarEstado(estado, caminho);
}

module.exports = {
  foiEnviado,
  marcarComoEnviado,
};
