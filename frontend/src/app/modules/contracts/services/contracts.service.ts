import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, delay, of } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { getContractSummaryMock, listContractsMock } from '../../../core/mocks/contracts.mock';
import {
  Contract,
  ContractFilters,
  ContractSummary,
  ExportFormat,
} from '../../../shared/models/contract.model';
import { Page } from '../../../shared/models/execution.model';
import {
  buildContractFilterParams,
  buildContractQuery,
} from '../../../shared/utils/contract-format';

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

  /**
   * Endereço de GET /api/contracts/export/ com os filtros da tela. É um link de download comum:
   * a API devolve o arquivo como anexo, com todos os contratos do filtro.
   * Sem API (useMocks) não há o que baixar: devolve null.
   */
  exportUrl(format: ExportFormat, filters: ContractFilters): string | null {
    if (environment.useMocks) return null;
    const params = new URLSearchParams({ format, ...buildContractFilterParams(filters) });
    return `${this.baseUrl}/export/?${params}`;
  }
}
