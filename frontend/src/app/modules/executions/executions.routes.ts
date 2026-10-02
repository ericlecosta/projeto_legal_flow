import { Routes } from '@angular/router';

import { ExecutionDetailPage } from './pages/execution-detail-page/execution-detail-page';
import { ExecutionListPage } from './pages/execution-list-page/execution-list-page';

export const EXECUTIONS_ROUTES: Routes = [
  { path: '', component: ExecutionListPage, title: 'Execuções · LMS RPA Monitor' },
  { path: ':id', component: ExecutionDetailPage, title: 'Detalhe da Execução · LMS RPA Monitor' },
];
