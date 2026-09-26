const API_BASE_URL = 'http://127.0.0.1:8000';

function getStoredToken() {
  return localStorage.getItem('fatec_token');
}

function setAuthHeader(headers = {}) {
  const token = getStoredToken();
  if (token) {
    return { ...headers, Authorization: `Bearer ${token}` };
  }
  return headers;
}

async function apiRequest(path, options = {}) {
  const headers = setAuthHeader({
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  });

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = typeof payload === 'object' ? payload.detail : payload;
    throw new Error(detail || 'Erro ao realizar a operação.');
  }

  return payload;
}

function showMessage(elementId, message, isError = false) {
  const el = document.getElementById(elementId);
  if (!el) return;

  el.textContent = message;
  el.style.color = isError ? '#b42318' : '#1f7a1f';
  el.style.display = 'block';
}

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');
  const avisoForm = document.getElementById('avisoForm');
  const filtroForm = document.getElementById('filtroForm');
  const logoutButton = document.getElementById('logoutButton');

  if (loginForm) {
    loginForm.addEventListener('submit', async (event) => {
      event.preventDefault();

      const ra = document.getElementById('loginRa')?.value.trim();
      const senha = document.getElementById('loginSenha')?.value.trim();
      const status = document.getElementById('loginStatus');

      if (!ra || !senha) {
        showMessage('loginStatus', 'Preencha RA e senha.', true);
        return;
      }

      try {
        const data = await apiRequest('/login', {
          method: 'POST',
          body: JSON.stringify({ ra, senha }),
        });

        localStorage.setItem('fatec_token', data.access_token);
        showMessage('loginStatus', 'Login realizado com sucesso! Redirecionando...', false);
        setTimeout(() => {
          window.location.href = 'comunicados.html';
        }, 700);
      } catch (error) {
        showMessage('loginStatus', error.message, true);
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener('submit', async (event) => {
      event.preventDefault();

      const payload = {
        ra: document.getElementById('cadRa')?.value.trim(),
        email: document.getElementById('cadEmail')?.value.trim(),
        disciplina: document.getElementById('cadDisciplina')?.value.trim(),
        senha: document.getElementById('cadSenha')?.value.trim(),
      };

      const status = document.getElementById('registerStatus');

      if (!payload.ra || !payload.email || !payload.disciplina || !payload.senha) {
        showMessage('registerStatus', 'Preencha todos os campos do cadastro.', true);
        return;
      }

      try {
        await apiRequest('/professores', {
          method: 'POST',
          body: JSON.stringify(payload),
        });

        showMessage('registerStatus', 'Cadastro realizado com sucesso! Redirecionando para o login...', false);
        registerForm.reset();

        setTimeout(() => {
          window.location.href = 'LoginProf.html';
        }, 1200);
      } catch (error) {
        showMessage('registerStatus', error.message, true);
      }
    });
  }

  if (logoutButton) {
    logoutButton.addEventListener('click', () => {
      localStorage.removeItem('fatec_token');
      window.location.href = 'LoginProf.html';
    });
  }

  if (avisoForm) {
    const token = getStoredToken();
    if (!token) {
      window.location.href = 'LoginProf.html';
      return;
    }

    async function carregarComunicados() {
      try {
        const params = new URLSearchParams();
        const curso = document.getElementById('filtroCurso')?.value || '';
        const semestre = document.getElementById('filtroSemestre')?.value || '';
        const categoria = document.getElementById('filtroCategoria')?.value || '';

        if (curso) params.append('curso', curso);
        if (semestre) params.append('semestre', semestre);
        if (categoria) params.append('categoria', categoria);

        const endpoint = params.toString() ? `/comunicados?${params.toString()}` : '/comunicados';
        const comunicados = await apiRequest(endpoint);

        const container = document.getElementById('quadroMensagens');
        if (!container) return;

        container.innerHTML = '';

        if (!comunicados.length) {
          const empty = document.createElement('div');
          empty.className = 'mensagem-card vazio';
          empty.textContent = 'Nenhum comunicado encontrado.';
          container.appendChild(empty);
          return;
        }

        comunicados.forEach((item) => {
          const card = document.createElement('div');
          card.className = 'mensagem-card';

          const titulo = document.createElement('strong');
          titulo.textContent = item.categoria.replace('_', ' ').toUpperCase();

          const texto = document.createElement('p');
          texto.textContent = item.mensagem;

          const meta = document.createElement('small');
          const cursoText = item.curso === 'todos' ? 'Todos os cursos' : item.curso;
          const semestreText = item.semestre ? ` • ${item.semestre}º semestre` : '';
          const enviadoText = item.enviado ? ' • Já enviado' : ' • Pendente';
          meta.textContent = `${cursoText}${semestreText}${enviadoText}`;

          const actions = document.createElement('div');
          actions.className = 'card-actions';

          const markButton = document.createElement('button');
          markButton.type = 'button';
          markButton.className = 'mini-btn';
          markButton.textContent = item.enviado ? 'Reabrir' : 'Marcar enviado';
          markButton.addEventListener('click', async () => {
            try {
              const novoEstado = !item.enviado;
              await apiRequest(`/comunicados/${item.id}/marcar-enviado`, {
                method: 'PATCH',
                body: JSON.stringify({ enviado: novoEstado }),
              });
              await carregarComunicados();
            } catch (error) {
              showMessage('avisoStatus', error.message, true);
            }
          });

          const deleteButton = document.createElement('button');
          deleteButton.type = 'button';
          deleteButton.className = 'mini-btn danger';
          deleteButton.textContent = 'Excluir';
          deleteButton.addEventListener('click', async () => {
            try {
              await apiRequest(`/comunicados/${item.id}`, { method: 'DELETE' });
              await carregarComunicados();
            } catch (error) {
              showMessage('avisoStatus', error.message, true);
            }
          });

          actions.appendChild(markButton);
          actions.appendChild(deleteButton);

          card.appendChild(titulo);
          card.appendChild(texto);
          card.appendChild(meta);
          card.appendChild(actions);
          container.appendChild(card);
        });
      } catch (error) {
        showMessage('avisoStatus', error.message, true);
      }
    }

    if (filtroForm) {
      filtroForm.addEventListener('submit', (event) => {
        event.preventDefault();
        carregarComunicados();
      });
    }

    avisoForm.addEventListener('submit', async (event) => {
      event.preventDefault();

      const payload = {
        mensagem: document.getElementById('avisoMensagem')?.value.trim(),
        curso: document.getElementById('avisoCurso')?.value.trim() || 'todos',
        semestre: document.getElementById('avisoSemestre')?.value || null,
        categoria: document.getElementById('avisoCategoria')?.value || 'aviso_geral',
        link: document.getElementById('avisoLink')?.value.trim() || null,
        data_expiracao: document.getElementById('avisoDataExpiracao')?.value || null,
      };

      if (!payload.mensagem) {
        showMessage('avisoStatus', 'Digite a mensagem do comunicado.', true);
        return;
      }

      try {
        await apiRequest('/comunicados', {
          method: 'POST',
          body: JSON.stringify(payload),
        });

        avisoForm.reset();
        showMessage('avisoStatus', 'Comunicado criado com sucesso.', false);
        await carregarComunicados();
      } catch (error) {
        showMessage('avisoStatus', error.message, true);
      }
    });

    carregarComunicados();
  }
});
