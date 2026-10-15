# LMS RPA Monitor — Front-end

Dashboard de execução e monitoramento do RPA LMS, em **Angular 22** (standalone, signals, zoneless) com **Tailwind CSS v4** e os tokens do **DXi Design Guide**, incluindo tema claro e escuro.

## Como rodar

```bash
cd frontend
npm install
npm start            # http://localhost:4200, com dados simulados
npm test -- --watch=false
npm run build        # gera dist/frontend com o environment de produção
```

## Estrutura (DXi Developer Guide, seção 6)

```text
src/
├── app/
│   ├── core/                     # Escopo global, não acessado diretamente pelas features
│   │   ├── interceptors/         # http-error.interceptor.ts
│   │   ├── mocks/                # rpa.mock.ts: dados simulados enquanto não há back-end
│   │   └── services/             # theme.service.ts: tema claro/escuro (singleton)
│   ├── layouts/
│   │   └── main-layout/          # Sidebar + área autenticada
│   ├── modules/                  # Uma feature por pasta, com rotas lazy-loaded
│   │   ├── overview/             # /visao-geral
│   │   └── executions/           # /execucoes e /execucoes/:id
│   └── shared/
│       ├── components/           # status-badge, progress-bar, sparkline
│       ├── models/               # Contratos de dados (Execution, Overview...)
│       ├── pipes/                # duration, relativeDateTime, clock...
│       └── utils/                # Funções de formatação
├── assets/                       # favicon e imagens
├── environments/                 # apiUrl, wsUrl, useMocks
├── fonts/                        # Inter e JetBrains Mono (self-hosted)
└── styles.css                    # Tokens do Design Guide + temas
```

## Tokens e temas

- As escalas do guia ficam em `styles.css` como CSS custom properties, por exemplo `var(--color-brand-800)` e `var(--color-n-900)`. Também existem como utilitários do Tailwind, por exemplo `bg-brand-800`.
- A paleta padrão do Tailwind está desligada. Só existem as cores do guia.
- Os componentes usam **papéis semânticos**, que mudam conforme o tema: `canvas`, `surface`, `surface-elevated`, `border-soft`, `fg`, `fg-muted`, `fg-subtle`, `fg-faint`, `primary`, `success`, `warning`, `danger` e `info`.
- O tema escuro é o padrão. O claro é aplicado com `<html data-theme="light">` e fica salvo no `localStorage`.

## Integração com o back-end (Django)

Com `useMocks: false` (que é o padrão em produção), os services chamam a API:

| Método | Endpoint | Retorno |
| --- | --- | --- |
| GET | `/api/overview/` | `Overview` |
| GET | `/api/executions/?period=7d&status=&flow=&page=1&page_size=10` | `{ count, results: Execution[] }` (paginação padrão do DRF) |
| GET | `/api/executions/:id/` | `ExecutionDetail` (etapas, logs e erro) |

Os modelos TypeScript estão em `src/app/shared/models` e usam camelCase. No Django, use `djangorestframework-camel-case` ou serializers com os mesmos nomes de campo.
