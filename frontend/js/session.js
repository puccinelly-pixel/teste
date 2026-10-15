/**
 * Guarda o token e os dados do usuário durante a sessão do navegador.
 *
 * Usa sessionStorage: o token some ao fechar a aba, reduzindo a janela
 * de exposição. O conteúdo da página nunca é inserido como HTML (ver ui.js),
 * o que mitiga o risco de XSS ler o token.
 */
const KEY = 'todo.session';

export function saveSession({ access_token: token, expires_in: expiresIn, usuario }) {
  const data = {
    token,
    usuario,
    expiraEm: Date.now() + expiresIn * 1000,
  };
  sessionStorage.setItem(KEY, JSON.stringify(data));
}

export function getSession() {
  try {
    const data = JSON.parse(sessionStorage.getItem(KEY));
    if (!data?.token || Date.now() >= data.expiraEm) {
      clearSession();
      return null;
    }
    return data;
  } catch {
    clearSession();
    return null;
  }
}

export function clearSession() {
  sessionStorage.removeItem(KEY);
}
