export const environment = {
  production: true,
  /** Base da API REST do back-end Django (servida pelo Nginx no mesmo domínio). */
  apiUrl: '/api',
  /** Canal WebSocket para logs e status de execução em tempo real. */
  wsUrl: '/ws',
  /** Quando true, os services usam dados simulados em vez de chamar a API. */
  useMocks: false,
};
