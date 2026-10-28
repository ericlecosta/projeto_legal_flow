import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { CONTRACTS_MOCK } from '../../../../core/mocks/contracts.mock';
import { BASE_IDEAL_COLUMNS, ContractSummary } from '../../../../shared/models/contract.model';
import { ContractListPage } from './contract-list-page';

const SUMMARY: ContractSummary = {
  total: 4,
  byProgressState: [
    { progressState: 'Legal Review in Progress', count: 3 },
    { progressState: 'Effective Contract', count: 1 },
  ],
  lastUpdatedAt: '2026-10-15T09:12:00-04:00',
  lastExecutionId: 1043,
};

/** Integração da página com o serviço real e o HttpClient (só a rede é simulada). */
describe('ContractListPage', () => {
  let fixture: ComponentFixture<ContractListPage>;
  let http: HttpTestingController;
  let el: HTMLElement;

  const listRequests = () => http.match((r) => r.url === '/api/contracts/');

  async function render() {
    await TestBed.configureTestingModule({
      imports: [ContractListPage],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    fixture = TestBed.createComponent(ContractListPage);
    http = TestBed.inject(HttpTestingController);
    el = fixture.nativeElement;
    fixture.detectChanges();
    await fixture.whenStable();
  }

  async function settle() {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  }

  afterEach(() => {
    http.verify();
    jest.useRealTimers();
  });

  it('mostra o resumo por status, a última atualização e os contratos', async () => {
    await render();
    http.expectOne('/api/contracts/summary/').flush(SUMMARY);
    listRequests()[0].flush({ count: 2, results: CONTRACTS_MOCK.slice(0, 2) });
    await settle();

    const chips = [...el.querySelectorAll('[role="group"] button')].map((b) =>
      b.textContent!.replace(/\s+/g, ' ').trim(),
    );
    expect(chips).toEqual(['Legal Review in Progress 3', 'Effective Contract 1']);
    expect(el.querySelector('[data-testid="last-update"]')!.textContent).toContain(
      'execução #1043',
    );

    // Cabeçalho e valores iguais aos da planilha Base Ideal
    const headers = [...el.querySelectorAll('thead th')].map((th) => th.textContent!.trim());
    expect(headers).toEqual([...BASE_IDEAL_COLUMNS]);

    const rows = el.querySelectorAll('[data-testid="contract-row"]');
    expect(rows).toHaveLength(2);
    const cells = Object.fromEntries(
      [...rows[1].querySelectorAll('td')].map((td, i) => [headers[i], td.textContent!.trim()]),
    );
    expect(cells['Contract number']).toBe(CONTRACTS_MOCK[1].contractNumber);
    expect(cells['Counterparty']).toBe('Norte Tech Engenharia Ltda');
    expect(cells['Progress State']).toBe('Effective Contract');
    expect(cells['Start date']).toBe('2026-12-01');
    expect(cells['End date']).toBe('2027-11-30');
    expect(cells['Contract currency']).toBe('USD');
    expect(cells['Amount']).toBe('11.145,04');
    expect(cells['Review completed']).toBe('');
    expect(el.textContent).toContain('Mostrando 1-2 de 2 contratos');
  });

  it('contratos sem status aparecem só como total, sem virar filtro selecionado', async () => {
    await render();
    http.expectOne('/api/contracts/summary/').flush({
      ...SUMMARY,
      total: 5,
      byProgressState: [...SUMMARY.byProgressState, { progressState: null, count: 1 }],
    });
    listRequests()[0].flush({ count: 5, results: CONTRACTS_MOCK });
    await settle();

    expect(el.querySelectorAll('[role="group"] button')).toHaveLength(2);
    expect(el.querySelector('[aria-pressed="true"]')).toBeNull();
    expect(
      el.querySelector('[data-testid="no-status-count"]')!.textContent!.replace(/\s+/g, ' ').trim(),
    ).toBe('(sem Progress State) 1');
  });

  it('filtra pelo status ao clicar no resumo e limpa o filtro', async () => {
    await render();
    http.expectOne('/api/contracts/summary/').flush(SUMMARY);
    listRequests()[0].flush({ count: 4, results: CONTRACTS_MOCK });
    await settle();

    (el.querySelector('[role="group"] button') as HTMLButtonElement).click();
    await settle();
    const filtered = listRequests();
    expect(filtered).toHaveLength(1);
    expect(filtered[0].request.params.get('progress_state')).toBe('Legal Review in Progress');
    filtered[0].flush({ count: 1, results: [CONTRACTS_MOCK[2]] });
    await settle();

    expect(el.querySelector('[aria-pressed="true"]')!.textContent).toContain(
      'Legal Review in Progress',
    );
    const clear = [...el.querySelectorAll('button')].find((b) =>
      b.textContent!.includes('Limpar filtros'),
    )!;
    clear.click();
    await settle();
    const cleared = listRequests();
    expect(cleared[0].request.params.has('progress_state')).toBe(false);
    cleared[0].flush({ count: 4, results: CONTRACTS_MOCK });
  });

  it('exporta nos formatos da planilha com os filtros da tela', async () => {
    await render();
    http.expectOne('/api/contracts/summary/').flush(SUMMARY);
    listRequests()[0].flush({ count: 4, results: CONTRACTS_MOCK });
    await settle();

    const toggle = el.querySelector('[data-testid="export-menu"] button') as HTMLButtonElement;
    expect(el.querySelector('[role="menu"]')).toBeNull();
    toggle.click();
    await settle();
    expect(toggle.getAttribute('aria-expanded')).toBe('true');
    const links = () =>
      [...el.querySelectorAll('[role="menuitem"]')].map((a) => a.getAttribute('href'));
    expect(links()).toEqual([
      '/api/contracts/export/?format=xlsx',
      '/api/contracts/export/?format=xls',
      '/api/contracts/export/?format=csv',
      '/api/contracts/export/?format=pdf',
    ]);
    expect(el.querySelector('[role="menu"]')!.textContent).toContain('Todos os contratos da base');

    // Com um status selecionado, o arquivo traz só os contratos desse filtro
    (el.querySelector('[role="group"] button') as HTMLButtonElement).click();
    await settle();
    listRequests()[0].flush({ count: 1, results: [CONTRACTS_MOCK[2]] });
    await settle();
    toggle.click();
    await settle();
    expect(links()[0]).toBe(
      '/api/contracts/export/?format=xlsx&progress_state=Legal+Review+in+Progress',
    );
    expect(el.querySelector('[role="menu"]')!.textContent).toContain('filtro atual (1)');

    // Escolher um formato fecha o menu; Esc e clique fora também
    (el.querySelector('[role="menuitem"]') as HTMLAnchorElement).dispatchEvent(
      new MouseEvent('click', { cancelable: true }),
    );
    await settle();
    expect(el.querySelector('[role="menu"]')).toBeNull();
    toggle.click();
    await settle();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    await settle();
    expect(el.querySelector('[role="menu"]')).toBeNull();
  });

  it('busca depois que a pessoa para de digitar', async () => {
    jest.useFakeTimers();
    await render();
    http.expectOne('/api/contracts/summary/').flush(SUMMARY);
    listRequests()[0].flush({ count: 4, results: CONTRACTS_MOCK });
    fixture.detectChanges();

    const input = el.querySelector('#contract-search') as HTMLInputElement;
    for (const value of ['n', 'no', 'norte']) {
      input.value = value;
      input.dispatchEvent(new Event('input'));
      fixture.detectChanges();
      jest.advanceTimersByTime(100);
    }
    expect(listRequests()).toHaveLength(0);

    jest.advanceTimersByTime(300);
    fixture.detectChanges();
    const searched = listRequests();
    expect(searched).toHaveLength(1);
    expect(searched[0].request.params.get('search')).toBe('norte');
    searched[0].flush({ count: 1, results: [CONTRACTS_MOCK[1]] });
  });

  it('explica como popular a base quando ela está vazia', async () => {
    await render();
    http
      .expectOne('/api/contracts/summary/')
      .flush({ ...SUMMARY, total: 0, byProgressState: [], lastUpdatedAt: null });
    listRequests()[0].flush({ count: 0, results: [] });
    await settle();

    expect(el.textContent).toContain('A base ainda está vazia');
    expect(el.querySelector('[role="group"]')).toBeNull();
  });

  it('mostra erro quando a API falha', async () => {
    await render();
    http
      .expectOne('/api/contracts/summary/')
      .flush('erro', { status: 500, statusText: 'Server Error' });
    listRequests()[0].flush('erro', { status: 500, statusText: 'Server Error' });
    await settle();

    const alerts = [...el.querySelectorAll('[role="alert"]')].map((a) => a.textContent!.trim());
    expect(alerts).toContain('Não foi possível carregar os contratos.');
    expect(alerts).toContain('Não foi possível carregar o resumo da base.');
  });
});
