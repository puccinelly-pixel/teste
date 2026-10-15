/**
 * Cliente HTTP da API: centraliza URL, token, timeout e tratamento de erros.
 */
import { API_URL } from './config.js';
import { getSession } from './session.js';

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/** Ouvinte chamado quando a API responde 401 (token expirado/inválido). */
let onUnauthorized = () => {};
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

/** Converte o "detail" do FastAPI (string ou lista de erros) em texto. */
function extractMessage(body, status) {
  const detail = body?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail
      .map((err) => (err.msg || '').replace(/^Value error, /, ''))
      .join(' ');
  }
  if (status >= 500) return 'Erro no servidor. Tente novamente.';
  return 'Não foi possível concluir a operação.';
}

async function request(path, { method = 'GET', body, auth = true, query } = {}) {
  const url = new URL(path, API_URL);
  if (query) {
    Object.entries(query).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v);
    });
  }

  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth) {
    const session = getSession();
    if (session) headers.Authorization = `Bearer ${session.token}`;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);

  let response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch {
    throw new ApiError(
      'Não foi possível conectar à API. Verifique se o backend está rodando.',
      0,
    );
  } finally {
    clearTimeout(timeout);
  }

  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && auth) onUnauthorized();
    throw new ApiError(extractMessage(data, response.status), response.status);
  }
  return data;
}

export const api = {
  register: (dados) => request('/auth/register', { method: 'POST', body: dados, auth: false }),
  login: (dados) => request('/auth/login', { method: 'POST', body: dados, auth: false }),
  me: () => request('/auth/me'),

  listTasks: (filtros) => request('/tasks', { query: filtros }),
  createTask: (dados) => request('/tasks', { method: 'POST', body: dados }),
  updateTask: (id, dados) => request(`/tasks/${encodeURIComponent(id)}`, { method: 'PATCH', body: dados }),
  deleteTask: (id) => request(`/tasks/${encodeURIComponent(id)}`, { method: 'DELETE' }),
};
