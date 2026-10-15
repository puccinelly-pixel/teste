/**
 * Controlador principal: alterna entre as telas e conecta eventos à API.
 */
import { api, ApiError, setUnauthorizedHandler } from './api.js';
import { PAGE_SIZE, STATUS_LABELS } from './config.js';
import { clearSession, getSession, saveSession } from './session.js';
import {
  $, $$, confirmDialog, debounce, renderTask, setFormError, toast, withBusy,
} from './ui.js';

const state = {
  filtros: { status: '', busca: '', ordem: 'recentes' },
  tarefas: [],
  total: 0,
  carregando: false,
};

// ---------------------------------------------------------------------------
// Navegação entre telas
// ---------------------------------------------------------------------------

function showAuth() {
  $('#app-view').hidden = true;
  $('#auth-view').hidden = false;
  $('#login-form input[name="email"]').focus();
}

function showApp() {
  const { usuario } = getSession();
  $('#user-name').textContent = `Olá, ${usuario.nome.split(' ')[0]}`;
  $('#auth-view').hidden = true;
  $('#app-view').hidden = false;
  loadTasks();
}

function logout(message) {
  clearSession();
  state.tarefas = [];
  $('#task-list').replaceChildren();
  $$('form').forEach((f) => f.reset());
  showAuth();
  if (message) toast(message, 'info');
}

setUnauthorizedHandler(() => logout('Sua sessão expirou. Entre novamente.'));

// ---------------------------------------------------------------------------
// Autenticação
// ---------------------------------------------------------------------------

function selectTab(tab) {
  const isLogin = tab === 'login';
  $('#tab-login').setAttribute('aria-selected', String(isLogin));
  $('#tab-register').setAttribute('aria-selected', String(!isLogin));
  $('#login-form').hidden = !isLogin;
  $('#register-form').hidden = isLogin;
  setFormError($('#login-form'));
  setFormError($('#register-form'));
  $(`#${isLogin ? 'login' : 'register'}-form input`).focus();
}

$('#tab-login').addEventListener('click', () => selectTab('login'));
$('#tab-register').addEventListener('click', () => selectTab('register'));

$('#login-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const { email, senha } = Object.fromEntries(new FormData(form));
  if (!email.trim() || !senha) {
    setFormError(form, 'Preencha e-mail e senha.');
    return;
  }
  setFormError(form);
  await withBusy(form, async () => {
    try {
      saveSession(await api.login({ email: email.trim(), senha }));
      form.reset();
      showApp();
    } catch (err) {
      setFormError(form, err.message);
    }
  });
});

$('#register-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const dados = Object.fromEntries(new FormData(form));

  const erros = [];
  if (dados.nome.trim().length < 2) erros.push('Informe seu nome.');
  if (!form.elements.email.checkValidity() || !dados.email) erros.push('E-mail inválido.');
  if (dados.senha.length < 8 || !/[A-Za-z]/.test(dados.senha) || !/\d/.test(dados.senha)) {
    erros.push('A senha precisa de 8+ caracteres, com letras e números.');
  }
  if (dados.senha !== dados.confirmacao) erros.push('As senhas não conferem.');
  if (erros.length) {
    setFormError(form, erros.join(' '));
    return;
  }

  setFormError(form);
  await withBusy(form, async () => {
    try {
      saveSession(await api.register({
        nome: dados.nome.trim(),
        email: dados.email.trim(),
        senha: dados.senha,
      }));
      form.reset();
      toast('Conta criada. Bem-vindo(a)!');
      showApp();
    } catch (err) {
      setFormError(form, err.message);
    }
  });
});

$('#logout-btn').addEventListener('click', () => logout('Você saiu da conta.'));

// ---------------------------------------------------------------------------
// Listagem
// ---------------------------------------------------------------------------

const taskHandlers = {
  onStatus: changeStatus,
  onEdit: openEdit,
  onDelete: removeTask,
};

function renderList() {
  const list = $('#task-list');
  list.replaceChildren(...state.tarefas.map((t) => renderTask(t, taskHandlers)));

  const vazio = state.tarefas.length === 0 && !state.carregando;
  $('#empty-state').hidden = !vazio;
  const filtrando = state.filtros.status || state.filtros.busca;
  $('#empty-text').textContent = filtrando
    ? 'Nenhuma tarefa corresponde aos filtros.'
    : 'Crie sua primeira tarefa no painel ao lado.';

  $('#load-more').hidden = state.tarefas.length >= state.total;

  const plural = state.total === 1 ? 'tarefa' : 'tarefas';
  $('#summary').textContent = state.total
    ? `${state.total} ${plural}${filtrando ? ' encontrada(s)' : ''}`
    : '';
}

async function loadTasks({ append = false } = {}) {
  state.carregando = true;
  $('#loading').hidden = append || state.tarefas.length > 0;
  try {
    const data = await api.listTasks({
      ...state.filtros,
      limit: PAGE_SIZE,
      offset: append ? state.tarefas.length : 0,
    });
    state.tarefas = append ? [...state.tarefas, ...data.items] : data.items;
    state.total = data.total;
  } catch (err) {
    if (err.status !== 401) toast(err.message, 'error');
  } finally {
    state.carregando = false;
    $('#loading').hidden = true;
    renderList();
  }
}

$$('.chip').forEach((chip) => {
  chip.addEventListener('click', () => {
    $$('.chip').forEach((c) => c.classList.toggle('is-active', c === chip));
    state.filtros.status = chip.dataset.status;
    loadTasks();
  });
});

$('#search').addEventListener('input', debounce((event) => {
  state.filtros.busca = event.target.value.trim();
  loadTasks();
}, 350));

$('#order').addEventListener('change', (event) => {
  state.filtros.ordem = event.target.value;
  loadTasks();
});

$('#load-more').addEventListener('click', () => loadTasks({ append: true }));

// ---------------------------------------------------------------------------
// Criação, edição e exclusão
// ---------------------------------------------------------------------------

function taskPayload(form) {
  const dados = Object.fromEntries(new FormData(form));
  return {
    titulo: dados.titulo.trim(),
    descricao: dados.descricao.trim() || null,
    status: dados.status,
  };
}

$('#task-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = taskPayload(form);
  if (!payload.titulo) {
    setFormError(form, 'Informe um título.');
    form.elements.titulo.focus();
    return;
  }
  setFormError(form);
  await withBusy(form, async () => {
    try {
      await api.createTask(payload);
      form.reset();
      form.elements.titulo.focus();
      toast('Tarefa adicionada.');
      await loadTasks();
    } catch (err) {
      if (err.status !== 401) setFormError(form, err.message);
    }
  });
});

async function changeStatus(task, status) {
  try {
    const atualizada = await api.updateTask(task.id, { status });
    replaceTask(atualizada);
    toast(`Marcada como “${STATUS_LABELS[status]}”.`);
  } catch (err) {
    if (err.status !== 401) toast(err.message, 'error');
    renderList(); // restaura o select ao valor anterior
  }
}

function replaceTask(atualizada) {
  const sairDoFiltro = state.filtros.status && atualizada.status !== state.filtros.status;
  if (sairDoFiltro) {
    state.tarefas = state.tarefas.filter((t) => t.id !== atualizada.id);
    state.total -= 1;
  } else {
    state.tarefas = state.tarefas.map((t) => (t.id === atualizada.id ? atualizada : t));
  }
  renderList();
}

const editDialog = $('#edit-dialog');
const editForm = $('#edit-form');

function openEdit(task) {
  editForm.elements.tarefa_id.value = task.id;
  editForm.elements.titulo.value = task.titulo;
  editForm.elements.descricao.value = task.descricao || '';
  editForm.elements.status.value = task.status;
  setFormError(editForm);
  editDialog.showModal();
  editForm.elements.titulo.focus();
}

$('[data-close]', editDialog).addEventListener('click', () => editDialog.close());

editForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = taskPayload(editForm);
  if (!payload.titulo) {
    setFormError(editForm, 'Informe um título.');
    return;
  }
  await withBusy(editForm, async () => {
    try {
      const atualizada = await api.updateTask(editForm.elements.tarefa_id.value, payload);
      editDialog.close();
      replaceTask(atualizada);
      toast('Tarefa atualizada.');
    } catch (err) {
      if (err.status === 401) editDialog.close();
      else setFormError(editForm, err.message);
    }
  });
});

async function removeTask(task) {
  const ok = await confirmDialog(`“${task.titulo}” será excluída permanentemente.`);
  if (!ok) return;
  try {
    await api.deleteTask(task.id);
    state.tarefas = state.tarefas.filter((t) => t.id !== task.id);
    state.total -= 1;
    renderList();
    toast('Tarefa excluída.');
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) loadTasks();
    if (err.status !== 401) toast(err.message, 'error');
  }
}

// ---------------------------------------------------------------------------
// Inicialização
// ---------------------------------------------------------------------------

if (getSession()) showApp();
else showAuth();
