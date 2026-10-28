import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { ContractSummary } from '../../../shared/models/contract.model';
import { ContractsService } from './contracts.service';

describe('ContractsService (integração com HttpClient)', () => {
  let service: ContractsService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ContractsService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('lista contratos com busca, status e paginação na query', () => {
    let count = -1;
    service
      .list({ search: 'norte', progressState: 'Effective Contract' }, 2, 20)
      .subscribe((page) => {
        count = page.count;
      });

    const req = http.expectOne((r) => r.url === '/api/contracts/');
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('search')).toBe('norte');
    expect(req.request.params.get('progress_state')).toBe('Effective Contract');
    expect(req.request.params.get('page')).toBe('2');
    expect(req.request.params.get('page_size')).toBe('20');
    req.flush({ count: 1, results: [] });

    expect(count).toBe(1);
  });

  it('monta o link de exportação com o formato e os filtros da tela, sem paginação', () => {
    expect(
      service.exportUrl('xlsx', { search: ' sesi & cia ', progressState: 'Review Completed' }),
    ).toBe(
      '/api/contracts/export/?format=xlsx&search=sesi+%26+cia&progress_state=Review+Completed',
    );
    expect(service.exportUrl('pdf', { search: '', progressState: '' })).toBe(
      '/api/contracts/export/?format=pdf',
    );
  });

  it('não envia filtros vazios', () => {
    service.list({ search: '  ', progressState: '' }, 1, 20).subscribe();
    const req = http.expectOne((r) => r.url === '/api/contracts/');
    expect(req.request.params.keys().sort()).toEqual(['page', 'page_size']);
    req.flush({ count: 0, results: [] });
  });

  it('busca o resumo da base', () => {
    const summary: ContractSummary = {
      total: 3,
      byProgressState: [],
      lastUpdatedAt: null,
      lastExecutionId: null,
    };
    let received: ContractSummary | undefined;
    service.summary().subscribe((data) => (received = data));
    http.expectOne('/api/contracts/summary/').flush(summary);
    expect(received).toEqual(summary);
  });
});
