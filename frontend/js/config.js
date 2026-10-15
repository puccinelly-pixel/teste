/**
 * Configuração do frontend.
 * Altere API_URL se a API estiver rodando em outro endereço/porta
 * (lembre-se de também liberar a origem em CORS_ORIGINS no backend
 * e em connect-src no <meta> CSP do index.html).
 */
export const API_URL = 'http://localhost:8000';

export const STATUS_LABELS = {
  pendente: 'Pendente',
  em_andamento: 'Em andamento',
  concluida: 'Concluída',
};

export const PAGE_SIZE = 20;
