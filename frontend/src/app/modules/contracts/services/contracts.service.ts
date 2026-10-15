import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, delay, of } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { getContractSummaryMock, listContractsMock } from '../../../core/mocks/contracts.mock';
import { Contract, ContractFilters, ContractSummary } from '../../../shared/models/contract.model';
import { Page } from '../../../shared/models/execution.model';
import { buildContractQuery } from '../../../shared/utils/contract-format';

@Injectable({ providedIn: 'root' })
export class ContractsService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/contracts`;

  /** GET /api/contracts/?search=&progress_state=&page=&page_size= */
  list(filters: ContractFilters, page: number, pageSize: number): Observable<Page<Contract>> {
    if (environment.useMocks)
      return of(listContractsMock(filters, page, pageSize)).pipe(delay(200));
    return this.http.get<Page<Contract>>(`${this.baseUrl}/`, {
      params: buildContractQuery(filters, page, pageSize),
    });
  }

  /** GET /api/contracts/summary/ — total por status e última atualização da base. */
  summary(): Observable<ContractSummary> {
    if (environment.useMocks) return of(getContractSummaryMock()).pipe(delay(200));
    return this.http.get<ContractSummary>(`${this.baseUrl}/summary/`);
  }
}
