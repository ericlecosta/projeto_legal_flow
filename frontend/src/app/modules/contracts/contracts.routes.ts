import { Routes } from '@angular/router';

import { ContractListPage } from './pages/contract-list-page/contract-list-page';

export const CONTRACTS_ROUTES: Routes = [
  { path: '', component: ContractListPage, title: 'Contratos · LMS RPA Monitor' },
];
