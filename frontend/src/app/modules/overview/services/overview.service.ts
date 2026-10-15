import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, delay, of } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { getOverviewMock } from '../../../core/mocks/rpa.mock';
import { Overview } from '../../../shared/models/overview.model';

@Injectable({ providedIn: 'root' })
export class OverviewService {
  private readonly http = inject(HttpClient);

  /** GET /api/overview/ — indicadores dos últimos 7 dias. */
  get(): Observable<Overview> {
    if (environment.useMocks) return of(getOverviewMock()).pipe(delay(250));
    return this.http.get<Overview>(`${environment.apiUrl}/overview/`);
  }
}
