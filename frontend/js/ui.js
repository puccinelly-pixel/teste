/**
 * Utilitários de interface. Todo texto vindo do usuário/API é inserido
 * via textContent (nunca innerHTML), prevenindo XSS.
 */
import { STATUS_LABELS } from './config.js';

export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

/** Cria um elemento com atributos e filhos de forma segura. */
export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  Object.entries(attrs).forEach(([key, value]) => {
    if (value === undefined || value === null || value === false) return;
    if (key === 'class') node.className = value;
    else if (key === 'dataset') Object.assign(node.dataset, value);
    else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? '' : value);
  });
  children.flat().forEach((child) => {
    if (child === null || child === undefined || child === false) return;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  });
  return node;
}

/** Mostra uma notificação temporária. */
export function toast(message, type = 'success') {
  const container = $('#toasts');
  const node = el('div', { class: `toast toast--${type}` }, message);
  container.append(node);
  setTimeout(() => {
    node.classList.add('is-leaving');
    node.addEventListener('animationend', () => node.remove(), { once: true });
  }, 3200);
}

export function setFormError(form, message = '') {
  $('.form__error', form).textContent = message;
}

/** Desabilita o botão de envio enquanto a promise roda (evita duplo clique). */
export async function withBusy(form, fn) {
  const button = $('button[type="submit"]', form);
  button.disabled = true;
  button.setAttribute('aria-busy', 'true');
  try {
    return await fn();
  } finally {
    button.disabled = false;
    button.removeAttribute('aria-busy');
  }
}

const dateFormat = new Intl.DateTimeFormat('pt-BR', {
  day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
});

export function formatDate(iso) {
  // A API devolve UTC; datas sem fuso são tratadas como UTC.
  const value = /[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`;
  return dateFormat.format(new Date(value));
}

/** Monta o <li> de uma tarefa. */
export function renderTask(task, handlers) {
  const statusSelect = el(
    'select',
    {
      class: `status status--${task.status}`,
      'aria-label': `Status da tarefa ${task.titulo}`,
      onchange: (e) => handlers.onStatus(task, e.target.value),
    },
    Object.entries(STATUS_LABELS).map(([value, label]) => el(
      'option',
      { value, selected: value === task.status },
      label,
    )),
  );

  return el(
    'li',
    { class: `task task--${task.status}`, dataset: { id: task.id } },
    el(
      'div',
      { class: 'task__main' },
      el('h3', { class: 'task__title' }, task.titulo),
      task.descricao ? el('p', { class: 'task__desc' }, task.descricao) : null,
      el(
        'p',
        { class: 'task__meta' },
        el('time', { datetime: task.data_criacao }, `Criada em ${formatDate(task.data_criacao)}`),
      ),
    ),
    el(
      'div',
      { class: 'task__actions' },
      statusSelect,
      el('button', {
        class: 'btn btn--ghost btn--sm',
        type: 'button',
        onclick: () => handlers.onEdit(task),
      }, 'Editar'),
      el('button', {
        class: 'btn btn--ghost btn--sm btn--danger-text',
        type: 'button',
        onclick: () => handlers.onDelete(task),
      }, 'Excluir'),
    ),
  );
}

/** Abre o diálogo de confirmação e resolve true se o usuário confirmar. */
export function confirmDialog(text) {
  const dialog = $('#confirm-dialog');
  $('#confirm-text', dialog).textContent = text;
  dialog.returnValue = '';
  dialog.showModal();
  return new Promise((resolve) => {
    dialog.addEventListener(
      'close',
      () => resolve(dialog.returnValue === 'confirm'),
      { once: true },
    );
  });
}

export function debounce(fn, wait = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
}
