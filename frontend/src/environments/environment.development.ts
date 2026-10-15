export const environment = {
  production: false,
  /** API FastAPI rodando localmente (uvicorn ou docker compose, porta 8000). */
  apiUrl: 'http://localhost:8000/api',
  wsUrl: 'ws://localhost:8000/ws',
  // Mude para true para trabalhar no front sem a API rodando (dados de core/mocks/rpa.mock.ts).
  useMocks: false,
};
