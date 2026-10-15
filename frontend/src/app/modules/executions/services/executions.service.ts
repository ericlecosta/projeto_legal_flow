import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, delay, of, throwError } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { getExecutionMock, listExecutionsMock } from '../../../core/mocks/rpa.mock';
import {
  Execution,
  ExecutionDetail,
  ExecutionFilters,
  SimulatedFlow,
  Page,
} from '../../../shared/models/execution.model';

const MOCK_ACTION_ERROR = 'Ação indisponível com dados simulados (environment.useMocks).';

@Injectable({ providedIn: 'root' })
export class ExecutionsService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/executions`;

  /** GET /api/executions/?period=&status=&flow=&page=&page_size= */
  list(filters: ExecutionFilters, page: number, pageSize: number): Observable<Page<Execution>> {
    if (environment.useMocks) return of(listExecutionsMock(filters, page, pageSize)).pipe(delay(200));

    let params = new HttpParams().set('period', filters.period).set('page', page).set('page_size', pageSize);
    if (filters.status !== 'all') params = params.set('status', filters.status);
    if (filters.flow !== 'all') params = params.set('flow', filters.flow);
    return this.http.get<Page<Execution>>(`${this.baseUrl}/`, { params });
  }

  /** GET /api/executions/:id/ — inclui etapas, logs e erro. */
  get(id: number): Observable<ExecutionDetail> {
    if (environment.useMocks) {
      const detail = getExecutionMock(id);
      return detail ? of(detail).pipe(delay(200)) : throwError(() => new Error(`Execução ${id} não encontrada`));
    }
    return this.http.get<ExecutionDetail>(`${this.baseUrl}/${id}/`);
  }

  /** POST /api/executions/ — dispara uma execução manual. 409 se já houver uma em andamento. */
  run(flow: SimulatedFlow, headless = true): Observable<ExecutionDetail> {
    if (environment.useMocks) return throwError(() => new Error(MOCK_ACTION_ERROR));
    return this.http.post<ExecutionDetail>(`${this.baseUrl}/`, { flow, headless });
  }

  /** POST /api/executions/:id/stop/ — pede a interrupção da execução em andamento. */
  stop(id: number): Observable<void> {
    if (environment.useMocks) return throwError(() => new Error(MOCK_ACTION_ERROR));
    return this.http.post<void>(`${this.baseUrl}/${id}/stop/`, {});
  }
}
