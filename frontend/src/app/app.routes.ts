import { Routes } from '@angular/router';

import { MainLayout } from './layouts/main-layout/main-layout';

export const routes: Routes = [
  {
    path: '',
    component: MainLayout,
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'visao-geral' },
      {
        path: 'visao-geral',
        loadChildren: () => import('./modules/overview/overview.routes').then((m) => m.OVERVIEW_ROUTES),
      },
      {
        path: 'contratos',
        loadChildren: () => import('./modules/contracts/contracts.routes').then((m) => m.CONTRACTS_ROUTES),
      },
      {
        path: 'execucoes',
        loadChildren: () =>
          import('./modules/executions/executions.routes').then((m) => m.EXECUTIONS_ROUTES),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
