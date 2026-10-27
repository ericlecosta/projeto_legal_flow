-- =============================================================================
-- Dump inicial do banco LMS Legal (gerado por scripts/export_db.py)
-- Carregado automaticamente na primeira subida do container lms_postgres
-- via /docker-entrypoint-initdb.d/01_seed.sql
-- =============================================================================

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

CREATE TABLE IF NOT EXISTS public.executions (
    id SERIAL PRIMARY KEY,
    flow VARCHAR(32) NOT NULL,
    status VARCHAR(16) NOT NULL,
    trigger VARCHAR(16) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    duration_seconds DOUBLE PRECISION,
    records INTEGER,
    error_title VARCHAR(255),
    error_message TEXT,
    error_screenshot_url VARCHAR(512)
);

CREATE INDEX IF NOT EXISTS ix_executions_started_at ON public.executions USING btree (started_at);
CREATE INDEX IF NOT EXISTS ix_executions_status ON public.executions USING btree (status);

CREATE TABLE IF NOT EXISTS public.execution_steps (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL REFERENCES public.executions(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    key VARCHAR(32) NOT NULL,
    label VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL,
    duration_seconds DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS ix_execution_steps_execution_id ON public.execution_steps USING btree (execution_id);

CREATE TABLE IF NOT EXISTS public.execution_logs (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL REFERENCES public.executions(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    level VARCHAR(16) NOT NULL,
    message TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_execution_logs_execution_id ON public.execution_logs USING btree (execution_id);

CREATE TABLE IF NOT EXISTS public.rpa_jobs (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL UNIQUE REFERENCES public.executions(id) ON DELETE CASCADE,
    requested_at TIMESTAMPTZ NOT NULL,
    claimed_at TIMESTAMPTZ,
    stop_requested BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_rpa_jobs_execution_id ON public.rpa_jobs USING btree (execution_id);

CREATE TABLE IF NOT EXISTS public.contracts (
    id SERIAL PRIMARY KEY,
    contract_number VARCHAR(32) NOT NULL UNIQUE,
    management_number VARCHAR(32),
    counterparty TEXT,
    contract_name TEXT,
    contract_type VARCHAR(128),
    requester VARCHAR(128),
    department VARCHAR(128),
    progress_state VARCHAR(64),
    legal_reviewer VARCHAR(128),
    period_start DATE,
    period_end DATE,
    review_requested_at DATE,
    legal_review_started_at DATE,
    review_completed_at DATE,
    consent_requested_at DATE,
    consent_completed_at DATE,
    approval_requested_at DATE,
    approval_completed_at DATE,
    effective_at DATE,
    biz_drop_completed_at DATE,
    currency VARCHAR(8),
    amount DOUBLE PRECISION,
    flags JSON NOT NULL,
    raw JSON NOT NULL,
    last_execution_id INTEGER REFERENCES public.executions(id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_contracts_contract_number ON public.contracts USING btree (contract_number);
CREATE INDEX IF NOT EXISTS ix_contracts_department ON public.contracts USING btree (department);
CREATE INDEX IF NOT EXISTS ix_contracts_progress_state ON public.contracts USING btree (progress_state);
CREATE INDEX IF NOT EXISTS ix_contracts_updated_at ON public.contracts USING btree (updated_at);

TRUNCATE TABLE
    public.contracts,
    public.rpa_jobs,
    public.execution_logs,
    public.execution_steps,
    public.executions
RESTART IDENTITY CASCADE;

-- Dados da tabela: executions (22 registros)
COPY public.executions (id, flow, status, trigger, started_at, finished_at, duration_seconds, records, error_title, error_message, error_screenshot_url) FROM stdin;
1	contract_extraction	failed	manual	2026-10-15 17:00:01.848946-04	2026-10-15 17:02:04.343375-04	122.5	\N	Execução interrompida	Execução interrompida pelo usuário.	\N
2	contract_extraction	failed	manual	2026-10-15 17:02:10.985568-04	2026-10-15 17:03:37.48638-04	86.5	\N	Execução interrompida	Execução interrompida pelo usuário.	\N
3	contract_extraction	failed	manual	2026-10-15 17:03:53.142279-04	2026-10-15 17:28:30.140241-04	1477	\N	Execução interrompida	Execução interrompida pelo usuário.	\N
4	contract_extraction	success	manual	2026-10-16 14:10:56.06399-04	2026-10-16 14:15:19.20701-04	263.1	\N	\N	\N	\N
5	contract_extraction	success	manual	2026-10-16 14:16:56.189222-04	2026-10-16 14:21:38.965928-04	282.8	\N	\N	\N	\N
6	contract_extraction	failed	manual	2026-10-16 14:30:29.651087-04	2026-10-16 14:30:32.322687-04	2.7	\N	Falha no login do LMS	Page.goto: net::ERR_NAME_NOT_RESOLVED at https://sso.lge.com/\nCall log:\n  - navigating to "https://sso.lge.com/", waiting until "domcontentloaded"\n	\N
7	contract_extraction	failed	manual	2026-10-16 14:30:51.247118-04	2026-10-16 14:32:29.106409-04	97.9	\N	Execução interrompida	A API foi reiniciada enquanto a execução estava em andamento.	\N
8	contract_extraction	success	manual	2026-10-16 14:32:46.98864-04	2026-10-16 14:37:22.792619-04	275.8	\N	\N	\N	\N
9	contract_extraction	failed	manual	2026-10-16 14:38:10.671962-04	2026-10-16 14:41:17.687715-04	187	\N	Execução interrompida	Execução interrompida pelo usuário.	\N
10	contract_extraction	failed	manual	2026-10-16 14:41:51.104019-04	2026-10-16 14:43:17.698248-04	86.6	\N	Execução interrompida	Execução interrompida pelo usuário.	\N
11	contract_extraction	success	manual	2026-10-16 15:04:58.794675-04	2026-10-16 15:12:12.613279-04	433.8	\N	\N	\N	\N
12	contract_extraction	failed	manual	2026-10-16 15:42:59.584685-04	2026-10-16 15:54:45.261512-04	705.7	\N	Execução interrompida	Execução interrompida pelo usuário.	\N
13	contract_extraction	failed	manual	2026-10-16 15:57:51.053859-04	2026-10-16 15:57:55.744196-04	4.7	\N	Falha no login do LMS	Page.goto: net::ERR_NAME_NOT_RESOLVED at https://sso.lge.com/\nCall log:\n  - navigating to "https://sso.lge.com/", waiting until "domcontentloaded"\n	\N
14	contract_extraction	failed	manual	2026-10-16 15:58:20.609006-04	2026-10-16 15:58:21.540149-04	0.9	\N	Falha no login do LMS	Page.goto: net::ERR_NAME_NOT_RESOLVED at https://sso.lge.com/\nCall log:\n  - navigating to "https://sso.lge.com/", waiting until "domcontentloaded"\n	\N
15	contract_extraction	failed	manual	2026-10-16 15:58:27.325941-04	2026-10-16 15:58:27.830057-04	0.5	\N	Falha no login do LMS	Page.goto: net::ERR_NAME_NOT_RESOLVED at https://sso.lge.com/\nCall log:\n  - navigating to "https://sso.lge.com/", waiting until "domcontentloaded"\n	\N
16	contract_extraction	failed	manual	2026-10-16 15:59:02.745622-04	2026-10-22 14:44:27.267842-04	513924.5	\N	Execução interrompida	A API foi reiniciada enquanto a execução estava em andamento.	\N
17	contract_extraction	failed	manual	2026-10-22 15:08:22.598803-04	2026-10-22 15:08:24.951439-04	2.4	\N	Falha no login do LMS	Page.goto: net::ERR_NAME_NOT_RESOLVED at https://sso.lge.com/\nCall log:\n  - navigating to "https://sso.lge.com/", waiting until "domcontentloaded"\n	\N
18	contract_extraction	success	manual	2026-10-27 14:58:59.285171-04	2026-10-27 15:56:54.957209-04	3475.7	45	\N	\N	\N
19	contract_extraction	failed	manual	2026-10-27 16:08:46.358295-04	2026-10-27 16:09:43.868189-04	57.5	\N	Execução interrompida	Execução interrompida pelo usuário.	\N
20	contract_extraction	success	manual	2026-10-27 16:10:46.707978-04	2026-10-27 16:20:34.301276-04	587.6	45	\N	\N	\N
21	contract_extraction	failed	manual	2026-10-27 16:28:22.262986-04	2026-10-27 16:28:36.642908-04	14.4	\N	Execução interrompida	Execução interrompida pelo usuário.	\N
22	contract_extraction	running	manual	2026-10-27 16:38:08.21167-04	\N	\N	\N	\N	\N	\N
\.
SELECT pg_catalog.setval(pg_get_serial_sequence('public.executions', 'id'), COALESCE((SELECT MAX(id) FROM public.executions), 1), (SELECT MAX(id) IS NOT NULL FROM public.executions));

-- Dados da tabela: execution_steps (76 registros)
COPY public.execution_steps (id, execution_id, position, key, label, status, duration_seconds) FROM stdin;
51	17	2	contract_details	Extração dos contratos	skipped	\N
1	1	0	lms_login	Login no LMS	failed	\N
2	1	1	report_download	Download do relatório	skipped	\N
3	1	2	contract_details	Extração dos contratos	skipped	\N
32	11	1	report_download	Download do relatório	success	11.2
4	2	0	lms_login	Login no LMS	failed	\N
5	2	1	report_download	Download do relatório	skipped	\N
6	2	2	contract_details	Extração dos contratos	skipped	\N
7	3	0	lms_login	Login no LMS	success	117.4
33	11	2	contract_details	Extração dos contratos	success	316.2
8	3	1	report_download	Download do relatório	success	11.7
9	3	2	contract_details	Extração dos contratos	failed	\N
10	4	0	lms_login	Login no LMS	success	99.7
11	4	1	report_download	Download do relatório	success	9.7
12	4	2	contract_details	Extração dos contratos	success	153.6
34	12	0	lms_login	Login no LMS	success	103.9
13	5	0	lms_login	Login no LMS	success	101.5
14	5	1	report_download	Download do relatório	success	8.6
35	12	1	report_download	Download do relatório	success	15.7
15	5	2	contract_details	Extração dos contratos	success	172.5
16	6	0	lms_login	Login no LMS	failed	2.6
17	6	1	report_download	Download do relatório	skipped	\N
18	6	2	contract_details	Extração dos contratos	skipped	\N
36	12	2	contract_details	Extração dos contratos	failed	\N
19	7	0	lms_login	Login no LMS	failed	\N
20	7	1	report_download	Download do relatório	skipped	\N
21	7	2	contract_details	Extração dos contratos	skipped	\N
22	8	0	lms_login	Login no LMS	success	97.7
23	8	1	report_download	Download do relatório	success	7.7
24	8	2	contract_details	Extração dos contratos	success	170.3
25	9	0	lms_login	Login no LMS	success	121.5
37	13	0	lms_login	Login no LMS	failed	4.7
26	9	1	report_download	Download do relatório	success	9.7
38	13	1	report_download	Download do relatório	skipped	\N
27	9	2	contract_details	Extração dos contratos	failed	\N
39	13	2	contract_details	Extração dos contratos	skipped	\N
28	10	0	lms_login	Login no LMS	failed	\N
29	10	1	report_download	Download do relatório	skipped	\N
30	10	2	contract_details	Extração dos contratos	skipped	\N
31	11	0	lms_login	Login no LMS	success	106.3
73	22	1	report_download	Download do relatório	success	7.1
40	14	0	lms_login	Login no LMS	failed	0.9
41	14	1	report_download	Download do relatório	skipped	\N
42	14	2	contract_details	Extração dos contratos	skipped	\N
52	18	0	lms_login	Login no LMS	success	156.6
43	15	0	lms_login	Login no LMS	failed	0.5
44	15	1	report_download	Download do relatório	skipped	\N
45	15	2	contract_details	Extração dos contratos	skipped	\N
62	20	0	lms_login	Login no LMS	success	103.5
46	16	0	lms_login	Login no LMS	success	112.5
53	18	1	report_download	Download do relatório	success	13.2
47	16	1	report_download	Download do relatório	success	16.2
67	21	0	lms_login	Login no LMS	failed	\N
48	16	2	contract_details	Extração dos contratos	failed	\N
54	18	2	contract_details	Extração dos contratos	success	3305.6
49	17	0	lms_login	Login no LMS	failed	2.3
50	17	1	report_download	Download do relatório	skipped	\N
63	20	1	report_download	Download do relatório	success	13.1
55	18	3	base_ideal	Tratamento da base	success	0
68	21	1	report_download	Download do relatório	skipped	\N
56	18	4	data_upload	Envio para o banco	success	0
64	20	2	contract_details	Extração dos contratos	success	470.7
57	19	0	lms_login	Login no LMS	failed	\N
58	19	1	report_download	Download do relatório	skipped	\N
59	19	2	contract_details	Extração dos contratos	skipped	\N
60	19	3	base_ideal	Tratamento da base	skipped	\N
61	19	4	data_upload	Envio para o banco	skipped	\N
69	21	2	contract_details	Extração dos contratos	skipped	\N
65	20	3	base_ideal	Tratamento da base	success	0
70	21	3	base_ideal	Tratamento da base	skipped	\N
66	20	4	data_upload	Envio para o banco	success	0
71	21	4	data_upload	Envio para o banco	skipped	\N
75	22	3	base_ideal	Tratamento da base	pending	\N
76	22	4	data_upload	Envio para o banco	pending	\N
72	22	0	lms_login	Login no LMS	success	104.5
74	22	2	contract_details	Extração dos contratos	running	\N
\.
SELECT pg_catalog.setval(pg_get_serial_sequence('public.execution_steps', 'id'), COALESCE((SELECT MAX(id) FROM public.execution_steps), 1), (SELECT MAX(id) IS NOT NULL FROM public.execution_steps));

-- Dados da tabela: execution_logs (1690 registros)
COPY public.execution_logs (id, execution_id, timestamp, level, message) FROM stdin;
1	1	2026-10-15 16:59:59.121434-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
2	2	2026-10-15 17:02:09.896269-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
3	3	2026-10-15 17:03:50.847494-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
4	3	2026-10-15 17:03:53.161434-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
5	3	2026-10-15 17:03:53.161649-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
6	3	2026-10-15 17:03:53.475558-04	info	1. Acessando página SSO: https://sso.lge.com/
7	3	2026-10-15 17:03:58.391233-04	info	2. Clicando em Self-service OTP (#OTP)...
8	3	2026-10-15 17:03:58.440509-04	info	3. Preenchendo senha e submetendo autenticação (#myButton)...
9	3	2026-10-15 17:04:02.220322-04	info	4. Clicando em OTP temporário (.tempPw)...
10	3	2026-10-15 17:04:03.096833-04	info	5. Tentativa 1/5 de validação do formulário...
11	3	2026-10-15 17:04:04.33206-04	info	Captcha reconhecido: 'mdb66'
12	3	2026-10-15 17:04:04.347154-04	info	Submetendo requisição e aguardando resposta da API...
13	3	2026-10-15 17:04:04.924305-04	info	Resposta do serviço: 0#Temporary password has been sent to your PC outlook e-mail and mobile office on your smart phone. If you don't use either PC outlook e-mail or mobile office, please contact SPoC center(1544-3766/82-1544-3766).#u6347663
14	3	2026-10-15 17:04:04.924434-04	info	OTP obtido com sucesso: u6347663
15	3	2026-10-15 17:04:04.959099-04	info	OTP temporário obtido para login: u6347663
16	3	2026-10-15 17:04:04.959209-04	info	Iniciando nova instância do navegador Playwright...
17	3	2026-10-15 17:04:05.213444-04	info	Navegando para o portal de login: https://sso.lge.com/
18	3	2026-10-15 17:04:06.102259-04	info	Preenchendo User ID e Senha corporativa...
19	3	2026-10-15 17:04:10.171036-04	info	Aguardando campo #OTPPASSWORD e preenchendo token...
20	3	2026-10-15 17:04:10.179663-04	info	Clicando no botão de login (#loginSsobtn)...
21	3	2026-10-15 17:04:14.118395-04	info	Navegando para a página do LMS: https://lms.lge.com/#/app/dashboard
22	3	2026-10-15 17:05:50.527763-04	info	Página posicionada com sucesso em: https://lms.lge.com/#/app/dashboard
23	3	2026-10-15 17:05:50.562415-04	info	Navegando para a URL de busca de contratos: https://lms.lge.com/#/app/contract/search
24	3	2026-10-15 17:05:53.5653-04	info	Filtrando por Subsidiary Code: LGESP...
25	3	2026-10-15 17:05:53.718554-04	info	Filtrando por período de data (Request Date): 3...
26	3	2026-10-15 17:06:02.127135-04	info	Iniciando o download do arquivo de exportação de contratos...
27	3	2026-10-15 17:06:02.220469-04	info	Relatório de contratos salvo com sucesso em: /app/downloads/relatorio_contratos.xlsx
28	3	2026-10-15 17:06:02.241457-04	info	Lendo planilha: /app/downloads/relatorio_contratos.xlsx
29	3	2026-10-15 17:06:02.358158-04	info	Linhas após filtro 'mao' em 'Department of the person in charge': 52 de 795
30	3	2026-10-15 17:06:02.358921-04	info	[1/52] Processando C2026833448
31	3	2026-10-15 17:06:02.358974-04	info	Pesquisando contrato: C2026833448
32	3	2026-10-15 17:07:34.55442-04	warning	Tentativa 1/3 de C2026833448 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
33	3	2026-10-15 17:07:34.556901-04	info	Pesquisando contrato: C2026833448
34	3	2026-10-15 17:08:49.679078-04	info	C2026833448 coletado em 167.3s
35	3	2026-10-15 17:08:49.679451-04	info	[2/52] Processando C2026833165
36	3	2026-10-15 17:08:49.679524-04	info	Pesquisando contrato: C2026833165
37	3	2026-10-15 17:08:52.2767-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
38	3	2026-10-15 17:09:44.905424-04	info	C2026833165 coletado em 55.2s
39	3	2026-10-15 17:09:44.905687-04	info	[3/52] Processando C2026833176
40	3	2026-10-15 17:09:44.905742-04	info	Pesquisando contrato: C2026833176
41	3	2026-10-15 17:09:47.190557-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
42	3	2026-10-15 17:10:42.244177-04	info	C2026833176 coletado em 57.3s
43	3	2026-10-15 17:10:42.244458-04	info	[4/52] Processando C2026832850
44	3	2026-10-15 17:10:42.244536-04	info	Pesquisando contrato: C2026832850
45	3	2026-10-15 17:10:44.94101-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
46	3	2026-10-15 17:11:44.388506-04	info	C2026832850 coletado em 62.1s
47	3	2026-10-15 17:11:44.388844-04	info	[5/52] Processando C2026831822
48	3	2026-10-15 17:11:44.407854-04	info	Pesquisando contrato: C2026831822
49	3	2026-10-15 17:11:49.04193-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
50	3	2026-10-15 17:12:59.998221-04	info	C2026831822 coletado em 75.6s
51	3	2026-10-15 17:12:59.998571-04	info	[6/52] Processando C2026831823
52	3	2026-10-15 17:12:59.99864-04	info	Pesquisando contrato: C2026831823
53	3	2026-10-15 17:13:03.773243-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
54	3	2026-10-15 17:14:02.963712-04	info	C2026831823 coletado em 63.0s
55	3	2026-10-15 17:14:02.964093-04	info	[7/52] Processando C2026831469
56	3	2026-10-15 17:14:02.964168-04	info	Pesquisando contrato: C2026831469
57	3	2026-10-15 17:14:05.367532-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
58	3	2026-10-15 17:15:07.159956-04	info	C2026831469 coletado em 64.2s
59	3	2026-10-15 17:15:07.160281-04	info	[8/52] Processando C2026830541
60	3	2026-10-15 17:15:07.160349-04	info	Pesquisando contrato: C2026830541
61	3	2026-10-15 17:15:18.22558-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
62	3	2026-10-15 17:16:29.122685-04	info	C2026830541 coletado em 82.0s
63	3	2026-10-15 17:16:29.122935-04	info	[9/52] Processando C2026830501
64	3	2026-10-15 17:16:29.12298-04	info	Pesquisando contrato: C2026830501
65	3	2026-10-15 17:16:33.529272-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
66	3	2026-10-15 17:17:34.926722-04	info	C2026830501 coletado em 65.8s
67	3	2026-10-15 17:17:34.926964-04	info	[10/52] Processando C2026830325
68	3	2026-10-15 17:17:34.943974-04	info	Pesquisando contrato: C2026830325
69	3	2026-10-15 17:17:38.534146-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
70	3	2026-10-15 17:18:33.707562-04	info	C2026830325 coletado em 58.8s
71	3	2026-10-15 17:18:33.707958-04	info	[11/52] Processando C2026830332
72	3	2026-10-15 17:18:33.708046-04	info	Pesquisando contrato: C2026830332
73	3	2026-10-15 17:18:37.512605-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
74	3	2026-10-15 17:19:31.871191-04	info	C2026830332 coletado em 58.2s
75	3	2026-10-15 17:19:31.871536-04	info	[12/52] Processando C2026830319
76	3	2026-10-15 17:19:31.871602-04	info	Pesquisando contrato: C2026830319
77	3	2026-10-15 17:19:35.325233-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
78	3	2026-10-15 17:20:39.058355-04	info	C2026830319 coletado em 67.2s
79	3	2026-10-15 17:20:39.058694-04	info	[13/52] Processando C2026830310
80	3	2026-10-15 17:20:39.058761-04	info	Pesquisando contrato: C2026830310
81	3	2026-10-15 17:20:44.066114-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
82	3	2026-10-15 17:21:38.983576-04	info	C2026830310 coletado em 59.9s
83	3	2026-10-15 17:21:38.983858-04	info	[14/52] Processando C2026830326
84	3	2026-10-15 17:21:38.983913-04	info	Pesquisando contrato: C2026830326
85	3	2026-10-15 17:21:42.868863-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
86	3	2026-10-15 17:22:42.383084-04	info	C2026830326 coletado em 63.4s
87	3	2026-10-15 17:22:42.383386-04	info	[15/52] Processando C2026830337
88	3	2026-10-15 17:22:42.401361-04	info	Pesquisando contrato: C2026830337
89	3	2026-10-15 17:22:45.447176-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
90	3	2026-10-15 17:23:44.709844-04	info	C2026830337 coletado em 62.3s
91	3	2026-10-15 17:23:44.71018-04	info	[16/52] Processando C2026830338
92	3	2026-10-15 17:23:44.710256-04	info	Pesquisando contrato: C2026830338
93	3	2026-10-15 17:23:47.518944-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
94	3	2026-10-15 17:24:59.441655-04	info	C2026830338 coletado em 74.7s
95	3	2026-10-15 17:24:59.441953-04	info	[17/52] Processando C2026830018
96	3	2026-10-15 17:24:59.442005-04	info	Pesquisando contrato: C2026830018
97	3	2026-10-15 17:25:05.716425-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
98	3	2026-10-15 17:26:14.436924-04	info	C2026830018 coletado em 75.0s
99	3	2026-10-15 17:26:14.437152-04	info	[18/52] Processando C2026830050
100	3	2026-10-15 17:26:14.437192-04	info	Pesquisando contrato: C2026830050
101	3	2026-10-15 17:26:21.037843-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
102	3	2026-10-15 17:27:15.555318-04	info	C2026830050 coletado em 61.1s
103	3	2026-10-15 17:27:15.555613-04	info	[19/52] Processando C2026829743
104	3	2026-10-15 17:27:15.555655-04	info	Pesquisando contrato: C2026829743
105	3	2026-10-15 17:27:18.184263-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
106	3	2026-10-15 17:28:19.331362-04	info	C2026829743 coletado em 63.8s
107	3	2026-10-15 17:28:19.33161-04	info	[20/52] Processando C2026829737
108	4	2026-10-16 14:10:54.039684-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
109	4	2026-10-16 14:10:56.082079-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
110	4	2026-10-16 14:10:56.082316-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
111	4	2026-10-16 14:10:56.814677-04	info	1. Acessando página SSO: https://sso.lge.com/
112	4	2026-10-16 14:11:02.177381-04	info	2. Clicando em Self-service OTP (#OTP)...
113	4	2026-10-16 14:11:02.247803-04	info	3. Preenchendo senha e submetendo autenticação (#myButton)...
114	4	2026-10-16 14:11:06.453546-04	info	4. Clicando em OTP temporário (.tempPw)...
115	4	2026-10-16 14:11:07.40975-04	info	5. Tentativa 1/5 de validação do formulário...
116	4	2026-10-16 14:11:08.798874-04	info	Captcha reconhecido: 'xxdry'
117	4	2026-10-16 14:11:08.815196-04	info	Submetendo requisição e aguardando resposta da API...
118	4	2026-10-16 14:11:09.400154-04	info	Resposta do serviço: 0#Temporary password has been sent to your PC outlook e-mail and mobile office on your smart phone. If you don't use either PC outlook e-mail or mobile office, please contact SPoC center(1544-3766/82-1544-3766).#15g92358
119	4	2026-10-16 14:11:09.400239-04	info	OTP obtido com sucesso: 15g92358
120	4	2026-10-16 14:11:09.429062-04	info	OTP temporário obtido para login: 15g92358
121	4	2026-10-16 14:11:09.429187-04	info	Iniciando nova instância do navegador Playwright...
122	4	2026-10-16 14:11:09.704772-04	info	Navegando para o portal de login: https://sso.lge.com/
123	4	2026-10-16 14:11:10.53768-04	info	Preenchendo User ID e Senha corporativa...
124	4	2026-10-16 14:11:14.611578-04	info	Aguardando campo #OTPPASSWORD e preenchendo token...
125	4	2026-10-16 14:11:14.620459-04	info	Clicando no botão de login (#loginSsobtn)...
126	4	2026-10-16 14:11:18.664669-04	info	Navegando para a página do LMS: https://lms.lge.com/#/app/dashboard
127	4	2026-10-16 14:12:35.804382-04	info	Página posicionada com sucesso em: https://lms.lge.com/#/app/dashboard
128	4	2026-10-16 14:12:35.829095-04	info	Navegando para a URL de busca de contratos: https://lms.lge.com/#/app/contract/search
129	4	2026-10-16 14:12:38.831722-04	info	Filtrando por Subsidiary Code: LGESP...
130	4	2026-10-16 14:12:38.995453-04	info	Filtrando por período de data (Request Date): 3...
131	4	2026-10-16 14:12:45.413199-04	info	Iniciando o download do arquivo de exportação de contratos...
132	4	2026-10-16 14:12:45.51493-04	info	Relatório de contratos salvo com sucesso em: /app/downloads/relatorio_contratos.xlsx
133	4	2026-10-16 14:12:45.536608-04	info	Lendo planilha: /app/downloads/relatorio_contratos.xlsx
134	4	2026-10-16 14:12:45.706439-04	info	Linhas após filtro 'mao' em 'Department of the person in charge': 52 de 789
135	4	2026-10-16 14:12:45.708608-04	info	Coletando 52 contratos com 3 frente(s) em paralelo
136	4	2026-10-16 14:12:45.708685-04	info	[1/52] Processando C2026833448 (frente 1)
137	4	2026-10-16 14:12:45.708708-04	info	Pesquisando contrato: C2026833448
138	4	2026-10-16 14:12:45.741298-04	info	[2/52] Processando C2026833165 (frente 2)
139	4	2026-10-16 14:12:45.741409-04	info	Pesquisando contrato: C2026833165
140	4	2026-10-16 14:12:46.200333-04	info	[3/52] Processando C2026833176 (frente 3)
141	4	2026-10-16 14:12:46.200415-04	info	Pesquisando contrato: C2026833176
142	4	2026-10-16 14:12:52.741276-04	warning	Contrato C2026833165 não encontrado na busca.
143	4	2026-10-16 14:12:52.741389-04	info	[4/52] Processando C2026832850 (frente 2)
144	4	2026-10-16 14:12:52.74144-04	info	Pesquisando contrato: C2026832850
145	4	2026-10-16 14:12:52.74669-04	warning	Contrato C2026833176 não encontrado na busca.
146	4	2026-10-16 14:12:52.746796-04	info	[5/52] Processando C2026831822 (frente 3)
147	4	2026-10-16 14:12:52.74685-04	info	Pesquisando contrato: C2026831822
148	4	2026-10-16 14:12:54.845591-04	warning	Contrato C2026832850 não encontrado na busca.
149	4	2026-10-16 14:12:54.84569-04	info	[6/52] Processando C2026831823 (frente 2)
150	4	2026-10-16 14:12:54.84573-04	info	Pesquisando contrato: C2026831823
151	4	2026-10-16 14:12:54.850626-04	warning	Contrato C2026831822 não encontrado na busca.
152	4	2026-10-16 14:12:54.850721-04	info	[7/52] Processando C2026831469 (frente 3)
153	4	2026-10-16 14:12:54.868039-04	info	Pesquisando contrato: C2026831469
154	4	2026-10-16 14:12:56.962919-04	warning	Contrato C2026831469 não encontrado na busca.
155	4	2026-10-16 14:12:56.963027-04	info	[8/52] Processando C2026830501 (frente 3)
156	4	2026-10-16 14:12:56.963074-04	info	Pesquisando contrato: C2026830501
157	4	2026-10-16 14:12:57.602238-04	warning	Contrato C2026831823 não encontrado na busca.
158	4	2026-10-16 14:12:57.60232-04	info	[9/52] Processando C2026830541 (frente 2)
159	4	2026-10-16 14:12:57.602346-04	info	Pesquisando contrato: C2026830541
160	4	2026-10-16 14:12:59.069196-04	warning	Contrato C2026830501 não encontrado na busca.
161	4	2026-10-16 14:12:59.069304-04	info	[10/52] Processando C2026830325 (frente 3)
162	4	2026-10-16 14:12:59.069349-04	info	Pesquisando contrato: C2026830325
163	4	2026-10-16 14:12:59.700362-04	warning	Contrato C2026830541 não encontrado na busca.
164	4	2026-10-16 14:12:59.700455-04	info	[11/52] Processando C2026830319 (frente 2)
165	4	2026-10-16 14:12:59.700497-04	info	Pesquisando contrato: C2026830319
166	4	2026-10-16 14:13:01.166108-04	warning	Contrato C2026830325 não encontrado na busca.
167	4	2026-10-16 14:13:01.166184-04	info	[12/52] Processando C2026830310 (frente 3)
168	4	2026-10-16 14:13:01.166204-04	info	Pesquisando contrato: C2026830310
169	4	2026-10-16 14:13:01.791892-04	warning	Contrato C2026830319 não encontrado na busca.
170	4	2026-10-16 14:13:01.791986-04	info	[13/52] Processando C2026830326 (frente 2)
171	4	2026-10-16 14:13:01.792029-04	info	Pesquisando contrato: C2026830326
172	4	2026-10-16 14:13:03.25577-04	warning	Contrato C2026830310 não encontrado na busca.
173	4	2026-10-16 14:13:03.274224-04	info	[14/52] Processando C2026830332 (frente 3)
174	4	2026-10-16 14:13:03.274296-04	info	Pesquisando contrato: C2026830332
175	4	2026-10-16 14:13:03.800308-04	warning	Contrato C2026830326 não encontrado na busca.
176	4	2026-10-16 14:13:03.80042-04	info	[15/52] Processando C2026830338 (frente 2)
177	4	2026-10-16 14:13:03.80047-04	info	Pesquisando contrato: C2026830338
178	4	2026-10-16 14:13:05.375481-04	warning	Contrato C2026830332 não encontrado na busca.
179	4	2026-10-16 14:13:05.375558-04	info	[16/52] Processando C2026830337 (frente 3)
180	4	2026-10-16 14:13:05.375578-04	info	Pesquisando contrato: C2026830337
181	4	2026-10-16 14:13:05.899521-04	warning	Contrato C2026830338 não encontrado na busca.
182	4	2026-10-16 14:13:05.899588-04	info	[17/52] Processando C2026830018 (frente 2)
183	4	2026-10-16 14:13:05.899613-04	info	Pesquisando contrato: C2026830018
184	4	2026-10-16 14:13:07.464514-04	warning	Contrato C2026830337 não encontrado na busca.
185	4	2026-10-16 14:13:07.464632-04	info	[18/52] Processando C2026830050 (frente 3)
186	4	2026-10-16 14:13:07.464685-04	info	Pesquisando contrato: C2026830050
187	4	2026-10-16 14:13:07.990453-04	warning	Contrato C2026830018 não encontrado na busca.
188	4	2026-10-16 14:13:07.990558-04	info	[19/52] Processando C2026829737 (frente 2)
189	4	2026-10-16 14:13:07.990605-04	info	Pesquisando contrato: C2026829737
190	4	2026-10-16 14:13:10.083197-04	warning	Contrato C2026829737 não encontrado na busca.
191	4	2026-10-16 14:13:10.083287-04	info	[20/52] Processando C2026829743 (frente 2)
192	4	2026-10-16 14:13:10.083331-04	info	Pesquisando contrato: C2026829743
193	4	2026-10-16 14:13:10.521902-04	warning	Contrato C2026830050 não encontrado na busca.
194	4	2026-10-16 14:13:10.521996-04	info	[21/52] Processando C2026829481 (frente 3)
195	4	2026-10-16 14:13:10.522017-04	info	Pesquisando contrato: C2026829481
196	4	2026-10-16 14:13:12.192102-04	warning	Contrato C2026829743 não encontrado na busca.
197	4	2026-10-16 14:13:12.192197-04	info	[22/52] Processando C2026829335 (frente 2)
198	4	2026-10-16 14:13:12.192239-04	info	Pesquisando contrato: C2026829335
199	4	2026-10-16 14:13:12.616196-04	warning	Contrato C2026829481 não encontrado na busca.
200	4	2026-10-16 14:13:12.616259-04	info	[23/52] Processando C2026829228 (frente 3)
201	4	2026-10-16 14:13:12.616283-04	info	Pesquisando contrato: C2026829228
202	4	2026-10-16 14:13:14.285633-04	warning	Contrato C2026829335 não encontrado na busca.
203	4	2026-10-16 14:13:14.285742-04	info	[24/52] Processando C2026828532 (frente 2)
204	4	2026-10-16 14:13:14.285791-04	info	Pesquisando contrato: C2026828532
205	4	2026-10-16 14:13:14.707276-04	warning	Contrato C2026829228 não encontrado na busca.
206	4	2026-10-16 14:13:14.707369-04	info	[25/52] Processando C2026828391 (frente 3)
207	4	2026-10-16 14:13:14.707411-04	info	Pesquisando contrato: C2026828391
208	4	2026-10-16 14:13:16.392259-04	warning	Contrato C2026828532 não encontrado na busca.
209	4	2026-10-16 14:13:16.392355-04	info	[26/52] Processando C2025811697 (frente 2)
210	4	2026-10-16 14:13:16.392396-04	info	Pesquisando contrato: C2025811697
211	4	2026-10-16 14:13:16.713085-04	warning	Contrato C2026828391 não encontrado na busca.
212	4	2026-10-16 14:13:16.713178-04	info	[27/52] Processando C2026827793 (frente 3)
213	4	2026-10-16 14:13:16.73284-04	info	Pesquisando contrato: C2026827793
214	4	2026-10-16 14:13:18.416572-04	warning	Contrato C2025811697 não encontrado na busca.
215	4	2026-10-16 14:13:18.416667-04	info	[28/52] Processando C2026827791 (frente 2)
216	4	2026-10-16 14:13:18.416708-04	info	Pesquisando contrato: C2026827791
217	4	2026-10-16 14:13:18.839665-04	warning	Contrato C2026827793 não encontrado na busca.
218	4	2026-10-16 14:13:18.839762-04	info	[29/52] Processando C2026827335 (frente 3)
219	4	2026-10-16 14:13:18.839801-04	info	Pesquisando contrato: C2026827335
220	4	2026-10-16 14:13:20.513609-04	warning	Contrato C2026827791 não encontrado na busca.
221	4	2026-10-16 14:13:20.513704-04	info	[30/52] Processando C2026827341 (frente 2)
222	4	2026-10-16 14:13:20.51375-04	info	Pesquisando contrato: C2026827341
223	4	2026-10-16 14:13:20.938599-04	warning	Contrato C2026827335 não encontrado na busca.
224	4	2026-10-16 14:13:20.938689-04	info	[31/52] Processando C2026827349 (frente 3)
225	4	2026-10-16 14:13:20.938716-04	info	Pesquisando contrato: C2026827349
226	4	2026-10-16 14:13:22.618545-04	warning	Contrato C2026827341 não encontrado na busca.
227	4	2026-10-16 14:13:22.618655-04	info	[32/52] Processando C2026827137 (frente 2)
228	4	2026-10-16 14:13:22.618683-04	info	Pesquisando contrato: C2026827137
229	4	2026-10-16 14:13:23.043259-04	warning	Contrato C2026827349 não encontrado na busca.
230	4	2026-10-16 14:13:23.043359-04	info	[33/52] Processando C2026827146 (frente 3)
231	4	2026-10-16 14:13:23.043398-04	info	Pesquisando contrato: C2026827146
232	4	2026-10-16 14:13:24.722234-04	warning	Contrato C2026827137 não encontrado na busca.
233	4	2026-10-16 14:13:24.73881-04	info	[34/52] Processando C2026827161 (frente 2)
234	4	2026-10-16 14:13:24.738869-04	info	Pesquisando contrato: C2026827161
235	4	2026-10-16 14:13:25.056913-04	warning	Contrato C2026827146 não encontrado na busca.
236	4	2026-10-16 14:13:25.057016-04	info	[35/52] Processando C2026827166 (frente 3)
237	4	2026-10-16 14:13:25.057063-04	info	Pesquisando contrato: C2026827166
238	4	2026-10-16 14:13:26.838897-04	warning	Contrato C2026827161 não encontrado na busca.
239	4	2026-10-16 14:13:26.838992-04	info	[36/52] Processando C2026827151 (frente 2)
240	4	2026-10-16 14:13:26.839033-04	info	Pesquisando contrato: C2026827151
241	4	2026-10-16 14:13:27.159261-04	warning	Contrato C2026827166 não encontrado na busca.
242	4	2026-10-16 14:13:27.15937-04	info	[37/52] Processando C2026826722 (frente 3)
243	4	2026-10-16 14:13:27.159414-04	info	Pesquisando contrato: C2026826722
244	4	2026-10-16 14:13:28.943911-04	warning	Contrato C2026827151 não encontrado na busca.
245	4	2026-10-16 14:13:28.944014-04	info	[38/52] Processando C2026826100 (frente 2)
246	4	2026-10-16 14:13:28.944052-04	info	Pesquisando contrato: C2026826100
247	4	2026-10-16 14:13:29.264167-04	warning	Contrato C2026826722 não encontrado na busca.
248	4	2026-10-16 14:13:29.264259-04	info	[39/52] Processando C2026825492 (frente 3)
249	4	2026-10-16 14:13:29.264302-04	info	Pesquisando contrato: C2026825492
250	4	2026-10-16 14:13:31.043172-04	warning	Contrato C2026826100 não encontrado na busca.
251	4	2026-10-16 14:13:31.043277-04	info	[40/52] Processando C2026825327 (frente 2)
252	4	2026-10-16 14:13:31.043319-04	info	Pesquisando contrato: C2026825327
1231	16	2026-10-16 16:14:44.604789-04	info	C2026830541 coletado em 78.8s
1232	16	2026-10-16 16:14:44.605101-04	info	[10/52] Processando C2026830325
1233	16	2026-10-16 16:14:44.605172-04	info	Pesquisando contrato: C2026830325
1234	16	2026-10-16 16:14:47.792188-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1235	16	2026-10-16 16:15:50.474889-04	info	C2026830325 coletado em 65.9s
1236	16	2026-10-16 16:15:50.4752-04	info	[11/52] Processando C2026830319
1237	16	2026-10-16 16:15:50.475261-04	info	Pesquisando contrato: C2026830319
1238	16	2026-10-16 16:15:52.818491-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1239	16	2026-10-16 16:17:13.442012-04	warning	Tela de detalhe ainda carregando após 15s; seguindo com o que já carregou. Requisições pendentes: https://lms.lge.com/api/invoice/selectCostBizLawFirmList
1240	16	2026-10-16 16:17:13.452845-04	info	C2026830319 coletado em 83.0s
1241	16	2026-10-16 16:17:13.453133-04	info	[12/52] Processando C2026830310
1242	16	2026-10-16 16:17:13.453179-04	info	Pesquisando contrato: C2026830310
1243	16	2026-10-16 16:18:44.037369-04	warning	Tentativa 1/3 de C2026830310 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
1244	16	2026-10-16 16:18:44.040566-04	info	Pesquisando contrato: C2026830310
1245	16	2026-10-16 16:19:52.977163-04	info	C2026830310 coletado em 159.5s
1246	16	2026-10-16 16:19:52.97746-04	info	[13/52] Processando C2026830326
1247	16	2026-10-16 16:19:52.977497-04	info	Pesquisando contrato: C2026830326
1248	16	2026-10-16 16:20:00.908366-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1249	16	2026-10-16 16:21:07.606695-04	info	C2026830326 coletado em 74.6s
1250	16	2026-10-16 16:21:07.606942-04	info	[14/52] Processando C2026830332
1251	16	2026-10-16 16:21:07.623438-04	info	Pesquisando contrato: C2026830332
1252	16	2026-10-16 16:21:11.487568-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1253	16	2026-10-16 16:22:14.348251-04	info	C2026830332 coletado em 66.7s
1254	16	2026-10-16 16:22:14.348691-04	info	[15/52] Processando C2026830338
1255	16	2026-10-16 16:22:14.34875-04	info	Pesquisando contrato: C2026830338
1256	16	2026-10-16 16:22:17.093514-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1257	16	2026-10-16 16:23:21.711739-04	info	C2026830338 coletado em 67.4s
1258	16	2026-10-16 16:23:21.712004-04	info	[16/52] Processando C2026830337
1259	16	2026-10-16 16:23:21.712049-04	info	Pesquisando contrato: C2026830337
1260	16	2026-10-16 16:23:24.509779-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1261	16	2026-10-16 16:24:28.69428-04	info	C2026830337 coletado em 67.0s
1262	16	2026-10-16 16:24:28.694593-04	info	[17/52] Processando C2026830018
1263	16	2026-10-16 16:24:28.694638-04	info	Pesquisando contrato: C2026830018
1264	16	2026-10-16 16:24:32.233441-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1265	16	2026-10-16 16:25:33.738693-04	info	C2026830018 coletado em 65.0s
1266	16	2026-10-16 16:25:33.738994-04	info	[18/52] Processando C2026830050
1267	16	2026-10-16 16:25:33.739038-04	info	Pesquisando contrato: C2026830050
1268	16	2026-10-16 16:25:40.250992-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1269	16	2026-10-16 16:26:38.28104-04	info	C2026830050 coletado em 64.5s
1270	16	2026-10-16 16:26:38.281435-04	info	[19/52] Processando C2026829737
1380	18	2026-10-27 15:01:49.197296-04	info	Lendo planilha: /app/downloads/relatorio_contratos.xlsx
1381	18	2026-10-27 15:01:49.275534-04	info	Linhas após filtro 'mao' em 'Department of the person in charge': 45 de 769
1382	18	2026-10-27 15:01:49.276458-04	info	[1/45] Processando C2026834490
1383	18	2026-10-27 15:01:49.276537-04	info	Pesquisando contrato: C2026834490
1384	18	2026-10-27 15:03:21.321651-04	warning	Tentativa 1/3 de C2026834490 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
1385	18	2026-10-27 15:03:21.324848-04	info	Pesquisando contrato: C2026834490
1386	18	2026-10-27 15:04:51.33479-04	info	C2026834490 coletado em 182.1s
1387	18	2026-10-27 15:04:51.335163-04	info	[2/45] Processando C2026834516
1388	18	2026-10-27 15:04:51.335235-04	info	Pesquisando contrato: C2026834516
1389	18	2026-10-27 15:04:54.256632-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1390	18	2026-10-27 15:06:01.154776-04	info	C2026834516 coletado em 69.8s
1391	18	2026-10-27 15:06:01.155113-04	info	[3/45] Processando C2026834065
1392	18	2026-10-27 15:06:01.155178-04	info	Pesquisando contrato: C2026834065
1393	18	2026-10-27 15:06:07.45421-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1394	18	2026-10-27 15:07:33.739933-04	info	C2026834065 coletado em 92.6s
1395	18	2026-10-27 15:07:33.74027-04	info	[4/45] Processando C2026833919
1396	18	2026-10-27 15:07:33.740347-04	info	Pesquisando contrato: C2026833919
1397	18	2026-10-27 15:07:36.134244-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1398	18	2026-10-27 15:08:57.970773-04	info	C2026833919 coletado em 84.2s
1399	18	2026-10-27 15:08:57.971102-04	info	[5/45] Processando C2026833448
1440	18	2026-10-27 15:19:47.956528-04	info	C2026830325 coletado em 137.1s
1441	18	2026-10-27 15:19:47.956852-04	info	[15/45] Processando C2026830332
1442	18	2026-10-27 15:19:47.956913-04	info	Pesquisando contrato: C2026830332
1443	18	2026-10-27 15:19:51.063585-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1444	18	2026-10-27 15:20:32.950063-04	info	C2026830332 coletado em 45.0s
1445	18	2026-10-27 15:20:32.950374-04	info	[16/45] Processando C2026830319
1446	18	2026-10-27 15:20:32.95044-04	info	Pesquisando contrato: C2026830319
1447	18	2026-10-27 15:20:36.240225-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1448	18	2026-10-27 15:21:32.743198-04	info	C2026830319 coletado em 59.8s
1449	18	2026-10-27 15:21:32.743469-04	info	[17/45] Processando C2026830310
1450	18	2026-10-27 15:21:32.743538-04	info	Pesquisando contrato: C2026830310
1451	18	2026-10-27 15:21:36.442444-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1452	18	2026-10-27 15:22:47.123416-04	info	C2026830310 coletado em 74.4s
1453	18	2026-10-27 15:22:47.123775-04	info	[18/45] Processando C2026830337
1454	18	2026-10-27 15:22:47.123842-04	info	Pesquisando contrato: C2026830337
1455	18	2026-10-27 15:22:49.88455-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1456	18	2026-10-27 15:23:53.278324-04	info	C2026830337 coletado em 66.2s
1457	18	2026-10-27 15:23:53.278684-04	info	[19/45] Processando C2026830338
1458	18	2026-10-27 15:23:53.278749-04	info	Pesquisando contrato: C2026830338
1459	18	2026-10-27 15:23:55.941771-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1497	18	2026-10-27 15:35:16.714888-04	info	Pesquisando contrato: C2026828532
1498	18	2026-10-27 15:36:39.380411-04	info	C2026828532 coletado em 173.2s
1499	18	2026-10-27 15:36:39.380724-04	info	[29/45] Processando C2026828391
253	4	2026-10-16 14:13:31.278414-04	warning	Contrato C2026825492 não encontrado na busca.
254	4	2026-10-16 14:13:31.278527-04	info	[41/52] Processando C2026825339 (frente 3)
255	4	2026-10-16 14:13:31.278571-04	info	Pesquisando contrato: C2026825339
256	4	2026-10-16 14:13:33.166729-04	warning	Contrato C2026825327 não encontrado na busca.
257	4	2026-10-16 14:13:33.166819-04	info	[42/52] Processando C2026825095 (frente 2)
258	4	2026-10-16 14:13:33.166858-04	info	Pesquisando contrato: C2026825095
259	4	2026-10-16 14:13:33.379772-04	warning	Contrato C2026825339 não encontrado na busca.
260	4	2026-10-16 14:13:33.379866-04	info	[43/52] Processando C2026825103 (frente 3)
261	4	2026-10-16 14:13:33.379907-04	info	Pesquisando contrato: C2026825103
262	4	2026-10-16 14:13:35.266606-04	warning	Contrato C2026825095 não encontrado na busca.
263	4	2026-10-16 14:13:35.266718-04	info	[44/52] Processando C2026824781 (frente 2)
264	4	2026-10-16 14:13:35.266772-04	info	Pesquisando contrato: C2026824781
265	4	2026-10-16 14:13:35.480904-04	warning	Contrato C2026825103 não encontrado na busca.
266	4	2026-10-16 14:13:35.481008-04	info	[45/52] Processando C2026824779 (frente 3)
267	4	2026-10-16 14:13:35.481051-04	info	Pesquisando contrato: C2026824779
268	4	2026-10-16 14:13:37.361828-04	warning	Contrato C2026824781 não encontrado na busca.
269	4	2026-10-16 14:13:37.361945-04	info	[46/52] Processando C2026824756 (frente 2)
270	4	2026-10-16 14:13:37.361998-04	info	Pesquisando contrato: C2026824756
271	4	2026-10-16 14:13:37.579241-04	warning	Contrato C2026824779 não encontrado na busca.
272	4	2026-10-16 14:13:37.579331-04	info	[47/52] Processando C2026824759 (frente 3)
273	4	2026-10-16 14:13:37.599065-04	info	Pesquisando contrato: C2026824759
274	4	2026-10-16 14:13:39.382585-04	warning	Contrato C2026824756 não encontrado na busca.
275	4	2026-10-16 14:13:39.382668-04	info	[48/52] Processando C2026824758 (frente 2)
276	4	2026-10-16 14:13:39.382694-04	info	Pesquisando contrato: C2026824758
277	4	2026-10-16 14:13:39.697952-04	warning	Contrato C2026824759 não encontrado na busca.
278	4	2026-10-16 14:13:39.69805-04	info	[49/52] Processando C2026824655 (frente 3)
279	4	2026-10-16 14:13:39.698093-04	info	Pesquisando contrato: C2026824655
280	4	2026-10-16 14:13:41.475113-04	warning	Contrato C2026824758 não encontrado na busca.
281	4	2026-10-16 14:13:41.475219-04	info	[50/52] Processando C2026824645 (frente 2)
282	4	2026-10-16 14:13:41.475264-04	info	Pesquisando contrato: C2026824645
283	4	2026-10-16 14:13:41.793066-04	warning	Contrato C2026824655 não encontrado na busca.
284	4	2026-10-16 14:13:41.793173-04	info	[51/52] Processando C2026824651 (frente 3)
285	4	2026-10-16 14:13:41.793232-04	info	Pesquisando contrato: C2026824651
286	4	2026-10-16 14:13:43.568104-04	warning	Contrato C2026824645 não encontrado na busca.
287	4	2026-10-16 14:13:43.56818-04	info	[52/52] Processando C2026824660 (frente 2)
288	4	2026-10-16 14:13:43.568201-04	info	Pesquisando contrato: C2026824660
289	4	2026-10-16 14:13:43.884202-04	warning	Contrato C2026824651 não encontrado na busca.
290	4	2026-10-16 14:13:45.643456-04	warning	Contrato C2026824660 não encontrado na busca.
291	4	2026-10-16 14:14:22.805049-04	warning	Tentativa 1/3 de C2026833448 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
292	4	2026-10-16 14:14:22.806957-04	info	Pesquisando contrato: C2026833448
293	4	2026-10-16 14:15:19.119698-04	info	C2026833448 coletado em 153.4s
294	4	2026-10-16 14:15:19.122715-04	info	52 contratos processados em 153.4s
295	4	2026-10-16 14:15:19.147894-04	info	Planilha consolidada salva em: /app/downloads/contract_review_management.xlsx (52 registros)
296	4	2026-10-16 14:15:19.164681-04	success	Fluxo concluído com sucesso.
297	5	2026-10-16 14:16:54.285892-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
298	5	2026-10-16 14:16:56.209723-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
299	5	2026-10-16 14:16:56.209991-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
300	5	2026-10-16 14:16:56.574834-04	info	1. Acessando página SSO: https://sso.lge.com/
301	5	2026-10-16 14:17:02.671258-04	info	2. Clicando em Self-service OTP (#OTP)...
302	5	2026-10-16 14:17:02.765265-04	info	3. Preenchendo senha e submetendo autenticação (#myButton)...
303	5	2026-10-16 14:17:07.963521-04	info	4. Clicando em OTP temporário (.tempPw)...
304	5	2026-10-16 14:17:08.897725-04	info	5. Tentativa 1/5 de validação do formulário...
305	5	2026-10-16 14:17:10.357001-04	info	Captcha reconhecido: 'kpykk'
306	5	2026-10-16 14:17:10.371001-04	info	Submetendo requisição e aguardando resposta da API...
307	5	2026-10-16 14:17:10.987775-04	info	Resposta do serviço: 0#Temporary password has been sent to your PC outlook e-mail and mobile office on your smart phone. If you don't use either PC outlook e-mail or mobile office, please contact SPoC center(1544-3766/82-1544-3766).#297b4764
308	5	2026-10-16 14:17:10.987845-04	info	OTP obtido com sucesso: 297b4764
309	5	2026-10-16 14:17:11.019711-04	info	OTP temporário obtido para login: 297b4764
310	5	2026-10-16 14:17:11.019792-04	info	Iniciando nova instância do navegador Playwright...
311	5	2026-10-16 14:17:11.30592-04	info	Navegando para o portal de login: https://sso.lge.com/
312	5	2026-10-16 14:17:12.219156-04	info	Preenchendo User ID e Senha corporativa...
313	5	2026-10-16 14:17:15.891476-04	info	Aguardando campo #OTPPASSWORD e preenchendo token...
314	5	2026-10-16 14:17:15.903622-04	info	Clicando no botão de login (#loginSsobtn)...
315	5	2026-10-16 14:17:19.928875-04	info	Navegando para a página do LMS: https://lms.lge.com/#/app/dashboard
316	5	2026-10-16 14:18:37.699158-04	info	Página posicionada com sucesso em: https://lms.lge.com/#/app/dashboard
317	5	2026-10-16 14:18:37.721175-04	info	Navegando para a URL de busca de contratos: https://lms.lge.com/#/app/contract/search
318	5	2026-10-16 14:18:40.723879-04	info	Filtrando por Subsidiary Code: LGESP...
319	5	2026-10-16 14:18:40.87561-04	info	Filtrando por período de data (Request Date): 3...
320	5	2026-10-16 14:18:46.266382-04	info	Iniciando o download do arquivo de exportação de contratos...
321	5	2026-10-16 14:18:46.367845-04	info	Relatório de contratos salvo com sucesso em: /app/downloads/relatorio_contratos.xlsx
322	5	2026-10-16 14:18:46.389688-04	info	Lendo planilha: /app/downloads/relatorio_contratos.xlsx
323	5	2026-10-16 14:18:46.51736-04	info	Linhas após filtro 'mao' em 'Department of the person in charge': 52 de 789
324	5	2026-10-16 14:18:46.519932-04	info	Coletando 52 contratos com 3 frente(s) em paralelo
325	5	2026-10-16 14:18:46.520008-04	info	[1/52] Processando C2026833448 (frente 1)
326	5	2026-10-16 14:18:46.520042-04	info	Pesquisando contrato: C2026833448
327	5	2026-10-16 14:18:46.55327-04	info	[2/52] Processando C2026833165 (frente 2)
328	5	2026-10-16 14:18:46.553403-04	info	Pesquisando contrato: C2026833165
329	5	2026-10-16 14:18:46.969682-04	info	[3/52] Processando C2026833176 (frente 3)
330	5	2026-10-16 14:18:46.969759-04	info	Pesquisando contrato: C2026833176
331	5	2026-10-16 14:18:50.845793-04	warning	Contrato C2026833165 não encontrado na busca.
332	5	2026-10-16 14:18:50.845916-04	info	[4/52] Processando C2026832850 (frente 2)
333	5	2026-10-16 14:18:50.845961-04	info	Pesquisando contrato: C2026832850
334	5	2026-10-16 14:18:50.850381-04	warning	Contrato C2026833176 não encontrado na busca.
335	5	2026-10-16 14:18:50.850487-04	info	[5/52] Processando C2026831822 (frente 3)
336	5	2026-10-16 14:18:50.85061-04	info	Pesquisando contrato: C2026831822
337	5	2026-10-16 14:18:52.953135-04	warning	Contrato C2026832850 não encontrado na busca.
338	5	2026-10-16 14:18:52.953246-04	info	[6/52] Processando C2026831823 (frente 2)
339	5	2026-10-16 14:18:52.953301-04	info	Pesquisando contrato: C2026831823
340	5	2026-10-16 14:18:55.052466-04	warning	Contrato C2026831823 não encontrado na busca.
341	5	2026-10-16 14:18:55.052583-04	info	[7/52] Processando C2026831469 (frente 2)
382	5	2026-10-16 14:19:09.616121-04	warning	Contrato C2026829737 não encontrado na busca.
383	5	2026-10-16 14:19:09.616197-04	info	[21/52] Processando C2026829481 (frente 3)
384	5	2026-10-16 14:19:09.616224-04	info	Pesquisando contrato: C2026829481
385	5	2026-10-16 14:19:11.505017-04	warning	Contrato C2026829743 não encontrado na busca.
386	5	2026-10-16 14:19:11.505184-04	info	[22/52] Processando C2026829335 (frente 2)
387	5	2026-10-16 14:19:11.505238-04	info	Pesquisando contrato: C2026829335
388	5	2026-10-16 14:19:11.72197-04	warning	Contrato C2026829481 não encontrado na busca.
389	5	2026-10-16 14:19:11.72209-04	info	[23/52] Processando C2026829228 (frente 3)
390	5	2026-10-16 14:19:11.722145-04	info	Pesquisando contrato: C2026829228
391	5	2026-10-16 14:19:13.510005-04	warning	Contrato C2026829335 não encontrado na busca.
392	5	2026-10-16 14:19:13.510121-04	info	[24/52] Processando C2026828532 (frente 2)
393	5	2026-10-16 14:19:13.510157-04	info	Pesquisando contrato: C2026828532
394	5	2026-10-16 14:19:13.830031-04	warning	Contrato C2026829228 não encontrado na busca.
395	5	2026-10-16 14:19:13.830129-04	info	[25/52] Processando C2026828391 (frente 3)
396	5	2026-10-16 14:19:13.83017-04	info	Pesquisando contrato: C2026828391
397	5	2026-10-16 14:19:15.61582-04	warning	Contrato C2026828532 não encontrado na busca.
398	5	2026-10-16 14:19:15.615922-04	info	[26/52] Processando C2025811697 (frente 2)
399	5	2026-10-16 14:19:15.615965-04	info	Pesquisando contrato: C2025811697
400	5	2026-10-16 14:19:15.936206-04	warning	Contrato C2026828391 não encontrado na busca.
401	5	2026-10-16 14:19:15.936313-04	info	[27/52] Processando C2026827793 (frente 3)
402	5	2026-10-16 14:19:15.956148-04	info	Pesquisando contrato: C2026827793
403	5	2026-10-16 14:19:17.629309-04	warning	Contrato C2025811697 não encontrado na busca.
404	5	2026-10-16 14:19:17.629379-04	info	[28/52] Processando C2026827791 (frente 2)
405	5	2026-10-16 14:19:17.629405-04	info	Pesquisando contrato: C2026827791
406	5	2026-10-16 14:19:18.048974-04	warning	Contrato C2026827793 não encontrado na busca.
407	5	2026-10-16 14:19:18.049072-04	info	[29/52] Processando C2026827335 (frente 3)
408	5	2026-10-16 14:19:18.049096-04	info	Pesquisando contrato: C2026827335
409	5	2026-10-16 14:19:19.726022-04	warning	Contrato C2026827791 não encontrado na busca.
410	5	2026-10-16 14:19:19.726125-04	info	[30/52] Processando C2026827341 (frente 2)
411	5	2026-10-16 14:19:19.726168-04	info	Pesquisando contrato: C2026827341
412	5	2026-10-16 14:19:20.152552-04	warning	Contrato C2026827335 não encontrado na busca.
413	5	2026-10-16 14:19:20.152681-04	info	[31/52] Processando C2026827349 (frente 3)
414	5	2026-10-16 14:19:20.15274-04	info	Pesquisando contrato: C2026827349
415	5	2026-10-16 14:19:21.737816-04	warning	Contrato C2026827341 não encontrado na busca.
416	5	2026-10-16 14:19:21.737906-04	info	[32/52] Processando C2026827137 (frente 2)
417	5	2026-10-16 14:19:21.737945-04	info	Pesquisando contrato: C2026827137
418	5	2026-10-16 14:19:22.160261-04	warning	Contrato C2026827349 não encontrado na busca.
419	5	2026-10-16 14:19:22.160373-04	info	[33/52] Processando C2026827146 (frente 3)
420	5	2026-10-16 14:19:22.160423-04	info	Pesquisando contrato: C2026827146
421	5	2026-10-16 14:19:23.841183-04	warning	Contrato C2026827137 não encontrado na busca.
442	5	2026-10-16 14:19:30.36815-04	warning	Contrato C2026825492 não encontrado na busca.
443	5	2026-10-16 14:19:30.368241-04	info	[41/52] Processando C2026825339 (frente 3)
444	5	2026-10-16 14:19:30.368282-04	info	Pesquisando contrato: C2026825339
445	5	2026-10-16 14:19:32.262146-04	warning	Contrato C2026825327 não encontrado na busca.
446	5	2026-10-16 14:19:32.262266-04	info	[42/52] Processando C2026825095 (frente 2)
447	5	2026-10-16 14:19:32.262315-04	info	Pesquisando contrato: C2026825095
448	5	2026-10-16 14:19:32.37282-04	warning	Contrato C2026825339 não encontrado na busca.
449	5	2026-10-16 14:19:32.372936-04	info	[43/52] Processando C2026825103 (frente 3)
450	5	2026-10-16 14:19:32.372977-04	info	Pesquisando contrato: C2026825103
451	5	2026-10-16 14:19:34.359718-04	warning	Contrato C2026825095 não encontrado na busca.
452	5	2026-10-16 14:19:34.359819-04	info	[44/52] Processando C2026824781 (frente 2)
453	5	2026-10-16 14:19:34.359859-04	info	Pesquisando contrato: C2026824781
454	5	2026-10-16 14:19:34.469687-04	warning	Contrato C2026825103 não encontrado na busca.
455	5	2026-10-16 14:19:34.469782-04	info	[45/52] Processando C2026824779 (frente 3)
456	5	2026-10-16 14:19:34.469828-04	info	Pesquisando contrato: C2026824779
457	5	2026-10-16 14:19:36.466592-04	warning	Contrato C2026824781 não encontrado na busca.
458	5	2026-10-16 14:19:36.466685-04	info	[46/52] Processando C2026824756 (frente 2)
459	5	2026-10-16 14:19:36.466733-04	info	Pesquisando contrato: C2026824756
460	5	2026-10-16 14:19:36.57654-04	warning	Contrato C2026824779 não encontrado na busca.
461	5	2026-10-16 14:19:36.576669-04	info	[47/52] Processando C2026824759 (frente 3)
1271	16	2026-10-16 16:26:38.30029-04	info	Pesquisando contrato: C2026829737
1272	16	2026-10-16 16:26:41.392603-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1273	16	2026-10-16 16:27:42.015792-04	info	C2026829737 coletado em 63.7s
1274	16	2026-10-16 16:27:42.016088-04	info	[20/52] Processando C2026829743
1275	16	2026-10-16 16:27:42.01613-04	info	Pesquisando contrato: C2026829743
1276	16	2026-10-16 16:27:44.403849-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1277	16	2026-10-16 16:28:45.449687-04	info	C2026829743 coletado em 63.4s
1278	16	2026-10-16 16:28:45.449972-04	info	[21/52] Processando C2026829481
1279	16	2026-10-16 16:28:45.450014-04	info	Pesquisando contrato: C2026829481
1280	16	2026-10-16 16:28:53.90228-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1281	16	2026-10-16 16:30:04.113856-04	info	C2026829481 coletado em 78.7s
1282	16	2026-10-16 16:30:04.114108-04	info	[22/52] Processando C2026829335
1283	16	2026-10-16 16:30:04.11415-04	info	Pesquisando contrato: C2026829335
1284	16	2026-10-16 16:30:06.879713-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1285	16	2026-10-16 16:31:22.546355-04	info	C2026829335 coletado em 78.4s
1286	16	2026-10-16 16:31:22.546645-04	info	[23/52] Processando C2026829228
1287	16	2026-10-16 16:31:22.546711-04	info	Pesquisando contrato: C2026829228
1288	16	2026-10-16 16:31:26.595423-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1289	16	2026-10-16 16:32:24.715587-04	info	C2026829228 coletado em 62.2s
342	5	2026-10-16 14:18:55.072101-04	info	Pesquisando contrato: C2026831469
343	5	2026-10-16 14:18:55.078368-04	warning	Contrato C2026831822 não encontrado na busca.
344	5	2026-10-16 14:18:55.078458-04	info	[8/52] Processando C2026830501 (frente 3)
345	5	2026-10-16 14:18:55.078507-04	info	Pesquisando contrato: C2026830501
346	5	2026-10-16 14:18:57.079944-04	warning	Contrato C2026831469 não encontrado na busca.
347	5	2026-10-16 14:18:57.080048-04	info	[9/52] Processando C2026830541 (frente 2)
348	5	2026-10-16 14:18:57.080078-04	info	Pesquisando contrato: C2026830541
349	5	2026-10-16 14:18:57.085811-04	warning	Contrato C2026830501 não encontrado na busca.
350	5	2026-10-16 14:18:57.085934-04	info	[10/52] Processando C2026830325 (frente 3)
351	5	2026-10-16 14:18:57.085984-04	info	Pesquisando contrato: C2026830325
352	5	2026-10-16 14:18:59.186072-04	warning	Contrato C2026830541 não encontrado na busca.
353	5	2026-10-16 14:18:59.186188-04	info	[11/52] Processando C2026830319 (frente 2)
354	5	2026-10-16 14:18:59.186246-04	info	Pesquisando contrato: C2026830319
355	5	2026-10-16 14:18:59.191134-04	warning	Contrato C2026830325 não encontrado na busca.
356	5	2026-10-16 14:18:59.191227-04	info	[12/52] Processando C2026830310 (frente 3)
357	5	2026-10-16 14:18:59.19127-04	info	Pesquisando contrato: C2026830310
358	5	2026-10-16 14:19:01.288168-04	warning	Contrato C2026830319 não encontrado na busca.
359	5	2026-10-16 14:19:01.288283-04	info	[13/52] Processando C2026830326 (frente 2)
360	5	2026-10-16 14:19:01.288324-04	info	Pesquisando contrato: C2026830326
361	5	2026-10-16 14:19:01.294015-04	warning	Contrato C2026830310 não encontrado na busca.
362	5	2026-10-16 14:19:01.313047-04	info	[14/52] Processando C2026830332 (frente 3)
363	5	2026-10-16 14:19:01.31312-04	info	Pesquisando contrato: C2026830332
364	5	2026-10-16 14:19:03.308009-04	warning	Contrato C2026830326 não encontrado na busca.
365	5	2026-10-16 14:19:03.308107-04	info	[15/52] Processando C2026830338 (frente 2)
366	5	2026-10-16 14:19:03.308149-04	info	Pesquisando contrato: C2026830338
367	5	2026-10-16 14:19:03.41805-04	warning	Contrato C2026830332 não encontrado na busca.
368	5	2026-10-16 14:19:03.418144-04	info	[16/52] Processando C2026830337 (frente 3)
369	5	2026-10-16 14:19:03.418185-04	info	Pesquisando contrato: C2026830337
370	5	2026-10-16 14:19:05.407374-04	warning	Contrato C2026830338 não encontrado na busca.
371	5	2026-10-16 14:19:05.407469-04	info	[17/52] Processando C2026830018 (frente 2)
372	5	2026-10-16 14:19:05.407497-04	info	Pesquisando contrato: C2026830018
373	5	2026-10-16 14:19:05.518138-04	warning	Contrato C2026830337 não encontrado na busca.
374	5	2026-10-16 14:19:05.518219-04	info	[18/52] Processando C2026830050 (frente 3)
375	5	2026-10-16 14:19:05.518249-04	info	Pesquisando contrato: C2026830050
376	5	2026-10-16 14:19:07.606077-04	warning	Contrato C2026830050 não encontrado na busca.
377	5	2026-10-16 14:19:07.606146-04	info	[19/52] Processando C2026829737 (frente 3)
378	5	2026-10-16 14:19:07.606167-04	info	Pesquisando contrato: C2026829737
379	5	2026-10-16 14:19:09.386627-04	warning	Contrato C2026830018 não encontrado na busca.
380	5	2026-10-16 14:19:09.386703-04	info	[20/52] Processando C2026829743 (frente 2)
381	5	2026-10-16 14:19:09.386733-04	info	Pesquisando contrato: C2026829743
422	5	2026-10-16 14:19:23.858275-04	info	[34/52] Processando C2026827161 (frente 2)
423	5	2026-10-16 14:19:23.858323-04	info	Pesquisando contrato: C2026827161
424	5	2026-10-16 14:19:24.176887-04	warning	Contrato C2026827146 não encontrado na busca.
425	5	2026-10-16 14:19:24.177008-04	info	[35/52] Processando C2026827166 (frente 3)
426	5	2026-10-16 14:19:24.177065-04	info	Pesquisando contrato: C2026827166
427	5	2026-10-16 14:19:25.956867-04	warning	Contrato C2026827161 não encontrado na busca.
428	5	2026-10-16 14:19:25.956932-04	info	[36/52] Processando C2026827151 (frente 2)
429	5	2026-10-16 14:19:25.956953-04	info	Pesquisando contrato: C2026827151
430	5	2026-10-16 14:19:26.273828-04	warning	Contrato C2026827166 não encontrado na busca.
431	5	2026-10-16 14:19:26.273912-04	info	[37/52] Processando C2026826722 (frente 3)
432	5	2026-10-16 14:19:26.273936-04	info	Pesquisando contrato: C2026826722
433	5	2026-10-16 14:19:28.043897-04	warning	Contrato C2026827151 não encontrado na busca.
434	5	2026-10-16 14:19:28.043971-04	info	[38/52] Processando C2026826100 (frente 2)
435	5	2026-10-16 14:19:28.043993-04	info	Pesquisando contrato: C2026826100
436	5	2026-10-16 14:19:28.360267-04	warning	Contrato C2026826722 não encontrado na busca.
437	5	2026-10-16 14:19:28.360341-04	info	[39/52] Processando C2026825492 (frente 3)
438	5	2026-10-16 14:19:28.360366-04	info	Pesquisando contrato: C2026825492
439	5	2026-10-16 14:19:30.133904-04	warning	Contrato C2026826100 não encontrado na busca.
440	5	2026-10-16 14:19:30.133975-04	info	[40/52] Processando C2026825327 (frente 2)
441	5	2026-10-16 14:19:30.134003-04	info	Pesquisando contrato: C2026825327
462	5	2026-10-16 14:19:36.595175-04	info	Pesquisando contrato: C2026824759
463	5	2026-10-16 14:19:38.489766-04	warning	Contrato C2026824756 não encontrado na busca.
464	5	2026-10-16 14:19:38.489864-04	info	[48/52] Processando C2026824758 (frente 2)
465	5	2026-10-16 14:19:38.489907-04	info	Pesquisando contrato: C2026824758
466	5	2026-10-16 14:19:38.701035-04	warning	Contrato C2026824759 não encontrado na busca.
467	5	2026-10-16 14:19:38.701128-04	info	[49/52] Processando C2026824655 (frente 3)
468	5	2026-10-16 14:19:38.701152-04	info	Pesquisando contrato: C2026824655
469	5	2026-10-16 14:19:40.587199-04	warning	Contrato C2026824758 não encontrado na busca.
470	5	2026-10-16 14:19:40.587299-04	info	[50/52] Processando C2026824645 (frente 2)
471	5	2026-10-16 14:19:40.587338-04	info	Pesquisando contrato: C2026824645
472	5	2026-10-16 14:19:40.798982-04	warning	Contrato C2026824655 não encontrado na busca.
473	5	2026-10-16 14:19:40.799057-04	info	[51/52] Processando C2026824651 (frente 3)
474	5	2026-10-16 14:19:40.79908-04	info	Pesquisando contrato: C2026824651
475	5	2026-10-16 14:19:42.677935-04	warning	Contrato C2026824645 não encontrado na busca.
476	5	2026-10-16 14:19:42.678028-04	info	[52/52] Processando C2026824660 (frente 2)
477	5	2026-10-16 14:19:42.678071-04	info	Pesquisando contrato: C2026824660
478	5	2026-10-16 14:19:42.893494-04	warning	Contrato C2026824651 não encontrado na busca.
479	5	2026-10-16 14:19:44.760896-04	warning	Contrato C2026824660 não encontrado na busca.
480	5	2026-10-16 14:20:20.89445-04	warning	Tentativa 1/3 de C2026833448 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
481	5	2026-10-16 14:20:20.896719-04	info	Pesquisando contrato: C2026833448
482	5	2026-10-16 14:21:38.882063-04	info	C2026833448 coletado em 172.4s
483	5	2026-10-16 14:21:38.88433-04	info	52 contratos processados em 172.4s
484	5	2026-10-16 14:21:38.913208-04	info	Planilha consolidada salva em: /app/downloads/contract_review_management.xlsx (52 registros)
485	5	2026-10-16 14:21:38.925925-04	success	Fluxo concluído com sucesso.
486	6	2026-10-16 14:30:29.660242-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
487	6	2026-10-16 14:30:29.660461-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
488	6	2026-10-16 14:30:30.023061-04	info	1. Acessando página SSO: https://sso.lge.com/
489	6	2026-10-16 14:30:32.307344-04	error	Falha no login do LMS: Page.goto: net::ERR_NAME_NOT_RESOLVED at https://sso.lge.com/\nCall log:\n  - navigating to "https://sso.lge.com/", waiting until "domcontentloaded"\n
490	7	2026-10-16 14:30:51.266936-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
491	7	2026-10-16 14:30:51.267114-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
492	7	2026-10-16 14:30:51.624108-04	info	1. Acessando página SSO: https://sso.lge.com/
493	7	2026-10-16 14:30:56.217694-04	info	2. Clicando em Self-service OTP (#OTP)...
494	7	2026-10-16 14:30:56.479507-04	info	3. Preenchendo senha e submetendo autenticação (#myButton)...
495	7	2026-10-16 14:31:00.658452-04	info	4. Clicando em OTP temporário (.tempPw)...
496	7	2026-10-16 14:31:01.531352-04	info	5. Tentativa 1/5 de validação do formulário...
497	7	2026-10-16 14:31:02.854659-04	info	Captcha reconhecido: 'y2epd'
498	7	2026-10-16 14:31:02.865649-04	info	Submetendo requisição e aguardando resposta da API...
499	7	2026-10-16 14:31:03.51309-04	info	Resposta do serviço: 0#Temporary password has been sent to your PC outlook e-mail and mobile office on your smart phone. If you don't use either PC outlook e-mail or mobile office, please contact SPoC center(1544-3766/82-1544-3766).#18859z35
500	7	2026-10-16 14:31:03.51316-04	info	OTP obtido com sucesso: 18859z35
501	7	2026-10-16 14:31:03.538829-04	info	OTP temporário obtido para login: 18859z35
502	7	2026-10-16 14:31:03.538963-04	info	Iniciando nova instância do navegador Playwright...
503	7	2026-10-16 14:31:03.775498-04	info	Navegando para o portal de login: https://sso.lge.com/
504	7	2026-10-16 14:31:04.641605-04	info	Preenchendo User ID e Senha corporativa...
505	7	2026-10-16 14:31:08.702056-04	info	Aguardando campo #OTPPASSWORD e preenchendo token...
506	7	2026-10-16 14:31:08.711373-04	info	Clicando no botão de login (#loginSsobtn)...
507	7	2026-10-16 14:31:12.760643-04	info	Navegando para a página do LMS: https://lms.lge.com/#/app/dashboard
508	8	2026-10-16 14:32:43.734637-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
509	8	2026-10-16 14:32:47.009714-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
510	8	2026-10-16 14:32:47.009989-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
511	8	2026-10-16 14:32:47.447832-04	info	1. Acessando página SSO: https://sso.lge.com/
512	8	2026-10-16 14:32:52.145293-04	info	2. Clicando em Self-service OTP (#OTP)...
513	8	2026-10-16 14:32:52.225704-04	info	3. Preenchendo senha e submetendo autenticação (#myButton)...
514	8	2026-10-16 14:32:56.679016-04	info	4. Clicando em OTP temporário (.tempPw)...
515	8	2026-10-16 14:32:57.676587-04	info	5. Tentativa 1/5 de validação do formulário...
516	8	2026-10-16 14:32:58.986085-04	info	Captcha reconhecido: 'b6w8p'
517	8	2026-10-16 14:32:59.001523-04	info	Submetendo requisição e aguardando resposta da API...
518	8	2026-10-16 14:32:59.651259-04	info	Resposta do serviço: 0#Temporary password has been sent to your PC outlook e-mail and mobile office on your smart phone. If you don't use either PC outlook e-mail or mobile office, please contact SPoC center(1544-3766/82-1544-3766).#863f6752
519	8	2026-10-16 14:32:59.651358-04	info	OTP obtido com sucesso: 863f6752
520	8	2026-10-16 14:32:59.687975-04	info	OTP temporário obtido para login: 863f6752
521	8	2026-10-16 14:32:59.688091-04	info	Iniciando nova instância do navegador Playwright...
522	8	2026-10-16 14:32:59.969904-04	info	Navegando para o portal de login: https://sso.lge.com/
523	8	2026-10-16 14:33:00.763311-04	info	Preenchendo User ID e Senha corporativa...
524	8	2026-10-16 14:33:05.666624-04	info	Aguardando campo #OTPPASSWORD e preenchendo token...
525	8	2026-10-16 14:33:05.676265-04	info	Clicando no botão de login (#loginSsobtn)...
526	8	2026-10-16 14:33:09.723654-04	info	Navegando para a página do LMS: https://lms.lge.com/#/app/dashboard
527	8	2026-10-16 14:34:24.704067-04	info	Página posicionada com sucesso em: https://lms.lge.com/#/app/dashboard
528	8	2026-10-16 14:34:24.736805-04	info	Navegando para a URL de busca de contratos: https://lms.lge.com/#/app/contract/search
529	8	2026-10-16 14:34:27.739743-04	info	Filtrando por Subsidiary Code: LGESP...
530	8	2026-10-16 14:34:27.925138-04	info	Filtrando por período de data (Request Date): 3...
531	8	2026-10-16 14:34:32.344654-04	info	Iniciando o download do arquivo de exportação de contratos...
532	8	2026-10-16 14:34:32.460256-04	info	Relatório de contratos salvo com sucesso em: /app/downloads/relatorio_contratos.xlsx
533	8	2026-10-16 14:34:32.484092-04	info	Lendo planilha: /app/downloads/relatorio_contratos.xlsx
534	8	2026-10-16 14:34:32.618379-04	info	Linhas após filtro 'mao' em 'Department of the person in charge': 52 de 789
535	8	2026-10-16 14:34:32.620383-04	info	Coletando 52 contratos com 3 frente(s) em paralelo
536	8	2026-10-16 14:34:32.620452-04	info	[1/52] Processando C2026833448 (frente 1)
537	8	2026-10-16 14:34:32.620474-04	info	Pesquisando contrato: C2026833448
538	8	2026-10-16 14:34:32.652933-04	info	[2/52] Processando C2026833165 (frente 2)
539	8	2026-10-16 14:34:32.653033-04	info	Pesquisando contrato: C2026833165
540	8	2026-10-16 14:34:33.062534-04	info	[3/52] Processando C2026833176 (frente 3)
541	8	2026-10-16 14:34:33.062648-04	info	Pesquisando contrato: C2026833176
542	8	2026-10-16 14:34:39.49163-04	warning	Contrato C2026833176 não encontrado na busca.
543	8	2026-10-16 14:34:39.491699-04	info	[4/52] Processando C2026832850 (frente 3)
544	8	2026-10-16 14:34:39.491725-04	info	Pesquisando contrato: C2026832850
545	8	2026-10-16 14:34:41.49527-04	warning	Contrato C2026833165 não encontrado na busca.
546	8	2026-10-16 14:34:41.495372-04	info	[5/52] Processando C2026831822 (frente 2)
547	8	2026-10-16 14:34:41.495418-04	info	Pesquisando contrato: C2026831822
548	8	2026-10-16 14:34:41.500392-04	warning	Contrato C2026832850 não encontrado na busca.
549	8	2026-10-16 14:34:41.500552-04	info	[6/52] Processando C2026831823 (frente 3)
550	8	2026-10-16 14:34:41.500615-04	info	Pesquisando contrato: C2026831823
551	8	2026-10-16 14:34:43.595264-04	warning	Contrato C2026831822 não encontrado na busca.
552	8	2026-10-16 14:34:43.595329-04	info	[7/52] Processando C2026831469 (frente 2)
553	8	2026-10-16 14:34:43.614736-04	info	Pesquisando contrato: C2026831469
554	8	2026-10-16 14:34:43.619481-04	warning	Contrato C2026831823 não encontrado na busca.
555	8	2026-10-16 14:34:43.619553-04	info	[8/52] Processando C2026830501 (frente 3)
556	8	2026-10-16 14:34:43.619574-04	info	Pesquisando contrato: C2026830501
557	8	2026-10-16 14:34:45.622657-04	warning	Contrato C2026831469 não encontrado na busca.
558	8	2026-10-16 14:34:45.622768-04	info	[9/52] Processando C2026830541 (frente 2)
559	8	2026-10-16 14:34:45.622813-04	info	Pesquisando contrato: C2026830541
560	8	2026-10-16 14:34:45.6281-04	warning	Contrato C2026830501 não encontrado na busca.
561	8	2026-10-16 14:34:45.628211-04	info	[10/52] Processando C2026830325 (frente 3)
562	8	2026-10-16 14:34:45.628253-04	info	Pesquisando contrato: C2026830325
563	8	2026-10-16 14:34:47.725332-04	warning	Contrato C2026830541 não encontrado na busca.
564	8	2026-10-16 14:34:47.725429-04	info	[11/52] Processando C2026830319 (frente 2)
565	8	2026-10-16 14:34:47.725453-04	info	Pesquisando contrato: C2026830319
566	8	2026-10-16 14:34:47.729897-04	warning	Contrato C2026830325 não encontrado na busca.
567	8	2026-10-16 14:34:47.729989-04	info	[12/52] Processando C2026830310 (frente 3)
568	8	2026-10-16 14:34:47.730014-04	info	Pesquisando contrato: C2026830310
569	8	2026-10-16 14:34:49.828266-04	warning	Contrato C2026830319 não encontrado na busca.
570	8	2026-10-16 14:34:49.828349-04	info	[13/52] Processando C2026830326 (frente 2)
571	8	2026-10-16 14:34:49.828372-04	info	Pesquisando contrato: C2026830326
572	8	2026-10-16 14:34:49.833106-04	warning	Contrato C2026830310 não encontrado na busca.
573	8	2026-10-16 14:34:49.851006-04	info	[14/52] Processando C2026830332 (frente 3)
574	8	2026-10-16 14:34:49.851116-04	info	Pesquisando contrato: C2026830332
575	8	2026-10-16 14:34:51.836305-04	warning	Contrato C2026830326 não encontrado na busca.
576	8	2026-10-16 14:34:51.836408-04	info	[15/52] Processando C2026830338 (frente 2)
577	8	2026-10-16 14:34:51.836434-04	info	Pesquisando contrato: C2026830338
578	8	2026-10-16 14:34:51.945976-04	warning	Contrato C2026830332 não encontrado na busca.
579	8	2026-10-16 14:34:51.946046-04	info	[16/52] Processando C2026830337 (frente 3)
580	8	2026-10-16 14:34:51.946068-04	info	Pesquisando contrato: C2026830337
581	8	2026-10-16 14:34:53.929301-04	warning	Contrato C2026830338 não encontrado na busca.
582	8	2026-10-16 14:34:53.929406-04	info	[17/52] Processando C2026830018 (frente 2)
583	8	2026-10-16 14:34:53.92943-04	info	Pesquisando contrato: C2026830018
584	8	2026-10-16 14:34:54.664832-04	warning	Contrato C2026830337 não encontrado na busca.
585	8	2026-10-16 14:34:54.664952-04	info	[18/52] Processando C2026830050 (frente 3)
586	8	2026-10-16 14:34:54.664979-04	info	Pesquisando contrato: C2026830050
587	8	2026-10-16 14:34:56.021611-04	warning	Contrato C2026830018 não encontrado na busca.
588	8	2026-10-16 14:34:56.021692-04	info	[19/52] Processando C2026829737 (frente 2)
589	8	2026-10-16 14:34:56.021719-04	info	Pesquisando contrato: C2026829737
590	8	2026-10-16 14:34:56.75395-04	warning	Contrato C2026830050 não encontrado na busca.
591	8	2026-10-16 14:34:56.754068-04	info	[20/52] Processando C2026829743 (frente 3)
592	8	2026-10-16 14:34:56.754092-04	info	Pesquisando contrato: C2026829743
593	8	2026-10-16 14:34:58.032328-04	warning	Contrato C2026829737 não encontrado na busca.
594	8	2026-10-16 14:34:58.032449-04	info	[21/52] Processando C2026829481 (frente 2)
595	8	2026-10-16 14:34:58.032512-04	info	Pesquisando contrato: C2026829481
596	8	2026-10-16 14:34:58.880737-04	warning	Contrato C2026829743 não encontrado na busca.
597	8	2026-10-16 14:34:58.880878-04	info	[22/52] Processando C2026829335 (frente 3)
598	8	2026-10-16 14:34:58.880925-04	info	Pesquisando contrato: C2026829335
599	8	2026-10-16 14:35:00.043195-04	warning	Contrato C2026829481 não encontrado na busca.
600	8	2026-10-16 14:35:00.04329-04	info	[23/52] Processando C2026829228 (frente 2)
601	8	2026-10-16 14:35:00.043331-04	info	Pesquisando contrato: C2026829228
602	8	2026-10-16 14:35:00.889447-04	warning	Contrato C2026829335 não encontrado na busca.
603	8	2026-10-16 14:35:00.889587-04	info	[24/52] Processando C2026828532 (frente 3)
604	8	2026-10-16 14:35:00.889643-04	info	Pesquisando contrato: C2026828532
605	8	2026-10-16 14:35:02.14939-04	warning	Contrato C2026829228 não encontrado na busca.
606	8	2026-10-16 14:35:02.149487-04	info	[25/52] Processando C2026828391 (frente 2)
607	8	2026-10-16 14:35:02.149518-04	info	Pesquisando contrato: C2026828391
608	8	2026-10-16 14:35:02.987267-04	warning	Contrato C2026828532 não encontrado na busca.
609	8	2026-10-16 14:35:02.987342-04	info	[26/52] Processando C2025811697 (frente 3)
610	8	2026-10-16 14:35:02.987363-04	info	Pesquisando contrato: C2025811697
611	8	2026-10-16 14:35:04.244639-04	warning	Contrato C2026828391 não encontrado na busca.
612	8	2026-10-16 14:35:04.244774-04	info	[27/52] Processando C2026827793 (frente 2)
613	8	2026-10-16 14:35:04.262925-04	info	Pesquisando contrato: C2026827793
614	8	2026-10-16 14:35:05.006374-04	warning	Contrato C2025811697 não encontrado na busca.
615	8	2026-10-16 14:35:05.006468-04	info	[28/52] Processando C2026827791 (frente 3)
616	8	2026-10-16 14:35:05.006514-04	info	Pesquisando contrato: C2026827791
617	8	2026-10-16 14:35:06.362603-04	warning	Contrato C2026827793 não encontrado na busca.
618	8	2026-10-16 14:35:06.362695-04	info	[29/52] Processando C2026827335 (frente 2)
619	8	2026-10-16 14:35:06.362718-04	info	Pesquisando contrato: C2026827335
620	8	2026-10-16 14:35:07.103835-04	warning	Contrato C2026827791 não encontrado na busca.
621	8	2026-10-16 14:35:07.103932-04	info	[30/52] Processando C2026827341 (frente 3)
622	8	2026-10-16 14:35:07.103976-04	info	Pesquisando contrato: C2026827341
623	8	2026-10-16 14:35:08.471013-04	warning	Contrato C2026827335 não encontrado na busca.
624	8	2026-10-16 14:35:08.471134-04	info	[31/52] Processando C2026827349 (frente 2)
625	8	2026-10-16 14:35:08.471188-04	info	Pesquisando contrato: C2026827349
626	8	2026-10-16 14:35:09.109522-04	warning	Contrato C2026827341 não encontrado na busca.
627	8	2026-10-16 14:35:09.109628-04	info	[32/52] Processando C2026827137 (frente 3)
628	8	2026-10-16 14:35:09.109671-04	info	Pesquisando contrato: C2026827137
629	8	2026-10-16 14:35:10.564687-04	warning	Contrato C2026827349 não encontrado na busca.
630	8	2026-10-16 14:35:10.564751-04	info	[33/52] Processando C2026827146 (frente 2)
631	8	2026-10-16 14:35:10.564777-04	info	Pesquisando contrato: C2026827146
632	8	2026-10-16 14:35:11.199792-04	warning	Contrato C2026827137 não encontrado na busca.
633	8	2026-10-16 14:35:11.217488-04	info	[34/52] Processando C2026827161 (frente 3)
634	8	2026-10-16 14:35:11.217551-04	info	Pesquisando contrato: C2026827161
635	8	2026-10-16 14:35:12.588484-04	warning	Contrato C2026827146 não encontrado na busca.
636	8	2026-10-16 14:35:12.588587-04	info	[35/52] Processando C2026827166 (frente 2)
637	8	2026-10-16 14:35:12.588631-04	info	Pesquisando contrato: C2026827166
638	8	2026-10-16 14:35:13.223665-04	warning	Contrato C2026827161 não encontrado na busca.
639	8	2026-10-16 14:35:13.223738-04	info	[36/52] Processando C2026827151 (frente 3)
640	8	2026-10-16 14:35:13.223762-04	info	Pesquisando contrato: C2026827151
641	8	2026-10-16 14:35:14.688221-04	warning	Contrato C2026827166 não encontrado na busca.
642	8	2026-10-16 14:35:14.688377-04	info	[37/52] Processando C2026826722 (frente 2)
643	8	2026-10-16 14:35:14.688422-04	info	Pesquisando contrato: C2026826722
644	8	2026-10-16 14:35:15.323341-04	warning	Contrato C2026827151 não encontrado na busca.
645	8	2026-10-16 14:35:15.323491-04	info	[38/52] Processando C2026826100 (frente 3)
646	8	2026-10-16 14:35:15.323557-04	info	Pesquisando contrato: C2026826100
647	8	2026-10-16 14:35:16.794748-04	warning	Contrato C2026826722 não encontrado na busca.
648	8	2026-10-16 14:35:16.794843-04	info	[39/52] Processando C2026825492 (frente 2)
649	8	2026-10-16 14:35:16.794884-04	info	Pesquisando contrato: C2026825492
650	8	2026-10-16 14:35:17.426947-04	warning	Contrato C2026826100 não encontrado na busca.
651	8	2026-10-16 14:35:17.427028-04	info	[40/52] Processando C2026825327 (frente 3)
652	8	2026-10-16 14:35:17.427057-04	info	Pesquisando contrato: C2026825327
653	8	2026-10-16 14:35:18.814226-04	warning	Contrato C2026825492 não encontrado na busca.
654	8	2026-10-16 14:35:18.814383-04	info	[41/52] Processando C2026825339 (frente 2)
655	8	2026-10-16 14:35:18.81444-04	info	Pesquisando contrato: C2026825339
656	8	2026-10-16 14:35:19.450353-04	warning	Contrato C2026825327 não encontrado na busca.
657	8	2026-10-16 14:35:19.450481-04	info	[42/52] Processando C2026825095 (frente 3)
658	8	2026-10-16 14:35:19.450529-04	info	Pesquisando contrato: C2026825095
659	8	2026-10-16 14:35:20.819854-04	warning	Contrato C2026825339 não encontrado na busca.
660	8	2026-10-16 14:35:20.819983-04	info	[43/52] Processando C2026825103 (frente 2)
661	8	2026-10-16 14:35:20.820029-04	info	Pesquisando contrato: C2026825103
662	8	2026-10-16 14:35:21.455674-04	warning	Contrato C2026825095 não encontrado na busca.
663	8	2026-10-16 14:35:21.455768-04	info	[44/52] Processando C2026824781 (frente 3)
664	8	2026-10-16 14:35:21.45581-04	info	Pesquisando contrato: C2026824781
665	8	2026-10-16 14:35:22.929296-04	warning	Contrato C2026825103 não encontrado na busca.
666	8	2026-10-16 14:35:22.929446-04	info	[45/52] Processando C2026824779 (frente 2)
667	8	2026-10-16 14:35:22.92951-04	info	Pesquisando contrato: C2026824779
668	8	2026-10-16 14:35:23.460476-04	warning	Contrato C2026824781 não encontrado na busca.
669	8	2026-10-16 14:35:23.460577-04	info	[46/52] Processando C2026824756 (frente 3)
670	8	2026-10-16 14:35:23.460621-04	info	Pesquisando contrato: C2026824756
671	8	2026-10-16 14:35:25.037236-04	warning	Contrato C2026824779 não encontrado na busca.
672	8	2026-10-16 14:35:25.037325-04	info	[47/52] Processando C2026824759 (frente 2)
673	8	2026-10-16 14:35:25.059441-04	info	Pesquisando contrato: C2026824759
674	8	2026-10-16 14:35:25.483346-04	warning	Contrato C2026824756 não encontrado na busca.
675	8	2026-10-16 14:35:25.48342-04	info	[48/52] Processando C2026824758 (frente 3)
676	8	2026-10-16 14:35:25.483445-04	info	Pesquisando contrato: C2026824758
677	8	2026-10-16 14:35:27.154424-04	warning	Contrato C2026824759 não encontrado na busca.
678	8	2026-10-16 14:35:27.154521-04	info	[49/52] Processando C2026824655 (frente 2)
679	8	2026-10-16 14:35:27.154552-04	info	Pesquisando contrato: C2026824655
680	8	2026-10-16 14:35:27.578144-04	warning	Contrato C2026824758 não encontrado na busca.
681	8	2026-10-16 14:35:27.578274-04	info	[50/52] Processando C2026824645 (frente 3)
682	8	2026-10-16 14:35:27.578325-04	info	Pesquisando contrato: C2026824645
683	8	2026-10-16 14:35:29.259199-04	warning	Contrato C2026824655 não encontrado na busca.
684	8	2026-10-16 14:35:29.259299-04	info	[51/52] Processando C2026824651 (frente 2)
685	8	2026-10-16 14:35:29.25934-04	info	Pesquisando contrato: C2026824651
686	8	2026-10-16 14:35:29.684951-04	warning	Contrato C2026824645 não encontrado na busca.
687	8	2026-10-16 14:35:29.685041-04	info	[52/52] Processando C2026824660 (frente 3)
688	8	2026-10-16 14:35:29.685084-04	info	Pesquisando contrato: C2026824660
689	8	2026-10-16 14:35:31.366715-04	warning	Contrato C2026824651 não encontrado na busca.
690	8	2026-10-16 14:35:31.78693-04	warning	Contrato C2026824660 não encontrado na busca.
691	8	2026-10-16 14:36:09.566396-04	warning	Tentativa 1/3 de C2026833448 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
692	8	2026-10-16 14:36:09.568624-04	info	Pesquisando contrato: C2026833448
693	8	2026-10-16 14:37:22.713432-04	info	C2026833448 coletado em 170.1s
694	8	2026-10-16 14:37:22.715519-04	info	52 contratos processados em 170.1s
695	8	2026-10-16 14:37:22.741385-04	info	Planilha consolidada salva em: /app/downloads/contract_review_management.xlsx (52 registros)
696	8	2026-10-16 14:37:22.756489-04	success	Fluxo concluído com sucesso.
697	9	2026-10-16 14:38:08.973533-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
698	9	2026-10-16 14:38:10.694708-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
699	9	2026-10-16 14:38:10.694921-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
700	9	2026-10-16 14:38:11.132017-04	info	1. Acessando página SSO: https://sso.lge.com/
701	9	2026-10-16 14:38:17.154679-04	info	2. Clicando em Self-service OTP (#OTP)...
702	9	2026-10-16 14:38:17.43046-04	info	3. Preenchendo senha e submetendo autenticação (#myButton)...
703	9	2026-10-16 14:38:22.028809-04	info	4. Clicando em OTP temporário (.tempPw)...
704	9	2026-10-16 14:38:22.963137-04	info	5. Tentativa 1/5 de validação do formulário...
705	9	2026-10-16 14:38:24.457765-04	info	Captcha reconhecido: 'cn6dp'
706	9	2026-10-16 14:38:24.47179-04	info	Submetendo requisição e aguardando resposta da API...
707	9	2026-10-16 14:38:25.054243-04	info	Resposta do serviço: 0#Temporary password has been sent to your PC outlook e-mail and mobile office on your smart phone. If you don't use either PC outlook e-mail or mobile office, please contact SPoC center(1544-3766/82-1544-3766).#501h3944
708	9	2026-10-16 14:38:25.05436-04	info	OTP obtido com sucesso: 501h3944
709	9	2026-10-16 14:38:25.084311-04	info	OTP temporário obtido para login: 501h3944
710	9	2026-10-16 14:38:25.084423-04	info	Iniciando nova instância do navegador Playwright...
711	9	2026-10-16 14:38:25.366709-04	info	Navegando para o portal de login: https://sso.lge.com/
712	9	2026-10-16 14:38:26.307435-04	info	Preenchendo User ID e Senha corporativa...
713	9	2026-10-16 14:38:30.467299-04	info	Aguardando campo #OTPPASSWORD e preenchendo token...
714	9	2026-10-16 14:38:30.478012-04	info	Clicando no botão de login (#loginSsobtn)...
715	9	2026-10-16 14:38:34.521941-04	info	Navegando para a página do LMS: https://lms.lge.com/#/app/dashboard
716	9	2026-10-16 14:40:12.197003-04	info	Página posicionada com sucesso em: https://lms.lge.com/#/app/dashboard
717	9	2026-10-16 14:40:12.224449-04	info	Navegando para a URL de busca de contratos: https://lms.lge.com/#/app/contract/search
718	9	2026-10-16 14:40:15.227672-04	info	Filtrando por Subsidiary Code: LGESP...
719	9	2026-10-16 14:40:15.395257-04	info	Filtrando por período de data (Request Date): 3...
720	9	2026-10-16 14:40:21.822187-04	info	Iniciando o download do arquivo de exportação de contratos...
721	9	2026-10-16 14:40:21.913824-04	info	Relatório de contratos salvo com sucesso em: /app/downloads/relatorio_contratos.xlsx
722	9	2026-10-16 14:40:21.936308-04	info	Lendo planilha: /app/downloads/relatorio_contratos.xlsx
723	9	2026-10-16 14:40:22.067627-04	info	Linhas após filtro 'mao' em 'Department of the person in charge': 52 de 789
724	9	2026-10-16 14:40:22.0698-04	info	Coletando 52 contratos com 3 frente(s) em paralelo
725	9	2026-10-16 14:40:22.069865-04	info	[1/52] Processando C2026833448 (frente 1)
726	9	2026-10-16 14:40:22.06989-04	info	Pesquisando contrato: C2026833448
727	9	2026-10-16 14:40:22.103614-04	info	[2/52] Processando C2026833165 (frente 2)
728	9	2026-10-16 14:40:22.103734-04	info	Pesquisando contrato: C2026833165
729	9	2026-10-16 14:40:22.553087-04	info	[3/52] Processando C2026833176 (frente 3)
730	9	2026-10-16 14:40:22.553213-04	info	Pesquisando contrato: C2026833176
731	9	2026-10-16 14:40:27.958904-04	warning	Contrato C2026833165 não encontrado na busca.
732	9	2026-10-16 14:40:27.958992-04	info	[4/52] Processando C2026832850 (frente 2)
733	9	2026-10-16 14:40:27.959015-04	info	Pesquisando contrato: C2026832850
734	9	2026-10-16 14:40:27.963484-04	warning	Contrato C2026833176 não encontrado na busca.
735	9	2026-10-16 14:40:27.963609-04	info	[5/52] Processando C2026831822 (frente 3)
736	9	2026-10-16 14:40:27.963657-04	info	Pesquisando contrato: C2026831822
737	9	2026-10-16 14:40:30.066792-04	warning	Contrato C2026832850 não encontrado na busca.
738	9	2026-10-16 14:40:30.066938-04	info	[6/52] Processando C2026831823 (frente 2)
739	9	2026-10-16 14:40:30.066986-04	info	Pesquisando contrato: C2026831823
740	9	2026-10-16 14:40:30.072773-04	warning	Contrato C2026831822 não encontrado na busca.
741	9	2026-10-16 14:40:30.072887-04	info	[7/52] Processando C2026831469 (frente 3)
742	9	2026-10-16 14:40:30.091517-04	info	Pesquisando contrato: C2026831469
743	9	2026-10-16 14:40:32.084253-04	warning	Contrato C2026831823 não encontrado na busca.
744	9	2026-10-16 14:40:32.084372-04	info	[8/52] Processando C2026830501 (frente 2)
745	9	2026-10-16 14:40:32.084418-04	info	Pesquisando contrato: C2026830501
746	9	2026-10-16 14:40:32.195631-04	warning	Contrato C2026831469 não encontrado na busca.
747	9	2026-10-16 14:40:32.195728-04	info	[9/52] Processando C2026830541 (frente 3)
748	9	2026-10-16 14:40:32.195771-04	info	Pesquisando contrato: C2026830541
749	9	2026-10-16 14:40:34.290079-04	warning	Contrato C2026830541 não encontrado na busca.
750	9	2026-10-16 14:40:34.290191-04	info	[10/52] Processando C2026830325 (frente 3)
751	9	2026-10-16 14:40:34.290249-04	info	Pesquisando contrato: C2026830325
752	9	2026-10-16 14:40:35.02577-04	warning	Contrato C2026830501 não encontrado na busca.
753	9	2026-10-16 14:40:35.025862-04	info	[11/52] Processando C2026830319 (frente 2)
754	9	2026-10-16 14:40:35.025893-04	info	Pesquisando contrato: C2026830319
755	9	2026-10-16 14:40:36.391878-04	warning	Contrato C2026830325 não encontrado na busca.
756	9	2026-10-16 14:40:36.391984-04	info	[12/52] Processando C2026830310 (frente 3)
757	9	2026-10-16 14:40:36.392008-04	info	Pesquisando contrato: C2026830310
758	9	2026-10-16 14:40:37.119063-04	warning	Contrato C2026830319 não encontrado na busca.
759	9	2026-10-16 14:40:37.119143-04	info	[13/52] Processando C2026830326 (frente 2)
760	9	2026-10-16 14:40:37.119171-04	info	Pesquisando contrato: C2026830326
761	9	2026-10-16 14:40:38.479383-04	warning	Contrato C2026830310 não encontrado na busca.
762	9	2026-10-16 14:40:38.529604-04	info	[14/52] Processando C2026830332 (frente 3)
763	9	2026-10-16 14:40:38.529649-04	info	Pesquisando contrato: C2026830332
764	9	2026-10-16 14:40:39.157452-04	warning	Contrato C2026830326 não encontrado na busca.
765	9	2026-10-16 14:40:39.157574-04	info	[15/52] Processando C2026830338 (frente 2)
766	9	2026-10-16 14:40:39.157603-04	info	Pesquisando contrato: C2026830338
767	9	2026-10-16 14:40:40.626925-04	warning	Contrato C2026830332 não encontrado na busca.
768	9	2026-10-16 14:40:40.627019-04	info	[16/52] Processando C2026830337 (frente 3)
769	9	2026-10-16 14:40:40.627069-04	info	Pesquisando contrato: C2026830337
770	9	2026-10-16 14:40:41.258197-04	warning	Contrato C2026830338 não encontrado na busca.
771	9	2026-10-16 14:40:41.258294-04	info	[17/52] Processando C2026830018 (frente 2)
772	9	2026-10-16 14:40:41.258338-04	info	Pesquisando contrato: C2026830018
773	9	2026-10-16 14:40:42.730269-04	warning	Contrato C2026830337 não encontrado na busca.
774	9	2026-10-16 14:40:42.730357-04	info	[18/52] Processando C2026830050 (frente 3)
775	9	2026-10-16 14:40:42.7304-04	info	Pesquisando contrato: C2026830050
776	9	2026-10-16 14:40:43.36102-04	warning	Contrato C2026830018 não encontrado na busca.
777	9	2026-10-16 14:40:43.361116-04	info	[19/52] Processando C2026829737 (frente 2)
778	9	2026-10-16 14:40:43.361167-04	info	Pesquisando contrato: C2026829737
779	9	2026-10-16 14:40:44.835565-04	warning	Contrato C2026830050 não encontrado na busca.
780	9	2026-10-16 14:40:44.835705-04	info	[20/52] Processando C2026829743 (frente 3)
781	9	2026-10-16 14:40:44.835766-04	info	Pesquisando contrato: C2026829743
802	9	2026-10-16 14:40:51.681072-04	info	Pesquisando contrato: C2026827793
803	9	2026-10-16 14:40:53.152695-04	warning	Contrato C2025811697 não encontrado na busca.
804	9	2026-10-16 14:40:53.152771-04	info	[28/52] Processando C2026827791 (frente 3)
805	9	2026-10-16 14:40:53.152799-04	info	Pesquisando contrato: C2026827791
806	9	2026-10-16 14:40:53.781129-04	warning	Contrato C2026827793 não encontrado na busca.
807	9	2026-10-16 14:40:53.781284-04	info	[29/52] Processando C2026827335 (frente 2)
808	9	2026-10-16 14:40:53.781308-04	info	Pesquisando contrato: C2026827335
809	9	2026-10-16 14:40:55.877463-04	warning	Contrato C2026827335 não encontrado na busca.
810	9	2026-10-16 14:40:55.87755-04	info	[30/52] Processando C2026827341 (frente 2)
811	9	2026-10-16 14:40:55.877578-04	info	Pesquisando contrato: C2026827341
812	9	2026-10-16 14:40:57.236621-04	warning	Contrato C2026827791 não encontrado na busca.
813	9	2026-10-16 14:40:57.236741-04	info	[31/52] Processando C2026827349 (frente 3)
814	9	2026-10-16 14:40:57.236775-04	info	Pesquisando contrato: C2026827349
815	9	2026-10-16 14:40:57.971876-04	warning	Contrato C2026827341 não encontrado na busca.
816	9	2026-10-16 14:40:57.971986-04	info	[32/52] Processando C2026827137 (frente 2)
817	9	2026-10-16 14:40:57.972031-04	info	Pesquisando contrato: C2026827137
818	9	2026-10-16 14:40:59.242728-04	warning	Contrato C2026827349 não encontrado na busca.
819	9	2026-10-16 14:40:59.242817-04	info	[33/52] Processando C2026827146 (frente 3)
820	9	2026-10-16 14:40:59.242842-04	info	Pesquisando contrato: C2026827146
821	9	2026-10-16 14:40:59.977815-04	warning	Contrato C2026827137 não encontrado na busca.
842	9	2026-10-16 14:41:07.574291-04	warning	Contrato C2026825492 não encontrado na busca.
843	9	2026-10-16 14:41:07.574405-04	info	[41/52] Processando C2026825339 (frente 3)
844	9	2026-10-16 14:41:07.574458-04	info	Pesquisando contrato: C2026825339
845	9	2026-10-16 14:41:08.309866-04	warning	Contrato C2026825327 não encontrado na busca.
846	9	2026-10-16 14:41:08.309968-04	info	[42/52] Processando C2026825095 (frente 2)
847	9	2026-10-16 14:41:08.310009-04	info	Pesquisando contrato: C2026825095
848	9	2026-10-16 14:41:09.673958-04	warning	Contrato C2026825339 não encontrado na busca.
849	9	2026-10-16 14:41:09.674062-04	info	[43/52] Processando C2026825103 (frente 3)
850	9	2026-10-16 14:41:09.674103-04	info	Pesquisando contrato: C2026825103
851	9	2026-10-16 14:41:10.409039-04	warning	Contrato C2026825095 não encontrado na busca.
852	9	2026-10-16 14:41:10.409133-04	info	[44/52] Processando C2026824781 (frente 2)
853	9	2026-10-16 14:41:10.40918-04	info	Pesquisando contrato: C2026824781
854	9	2026-10-16 14:41:11.782868-04	warning	Contrato C2026825103 não encontrado na busca.
855	9	2026-10-16 14:41:11.782985-04	info	[45/52] Processando C2026824779 (frente 3)
856	9	2026-10-16 14:41:11.783037-04	info	Pesquisando contrato: C2026824779
857	9	2026-10-16 14:41:12.418907-04	warning	Contrato C2026824781 não encontrado na busca.
858	9	2026-10-16 14:41:12.419005-04	info	[46/52] Processando C2026824756 (frente 2)
859	9	2026-10-16 14:41:12.419049-04	info	Pesquisando contrato: C2026824756
860	9	2026-10-16 14:41:13.790988-04	warning	Contrato C2026824779 não encontrado na busca.
782	9	2026-10-16 14:40:45.380103-04	warning	Contrato C2026829737 não encontrado na busca.
783	9	2026-10-16 14:40:45.380231-04	info	[21/52] Processando C2026829481 (frente 2)
784	9	2026-10-16 14:40:45.380287-04	info	Pesquisando contrato: C2026829481
785	9	2026-10-16 14:40:46.949384-04	warning	Contrato C2026829743 não encontrado na busca.
786	9	2026-10-16 14:40:46.949507-04	info	[22/52] Processando C2026829335 (frente 3)
787	9	2026-10-16 14:40:46.949564-04	info	Pesquisando contrato: C2026829335
788	9	2026-10-16 14:40:47.47899-04	warning	Contrato C2026829481 não encontrado na busca.
789	9	2026-10-16 14:40:47.479084-04	info	[23/52] Processando C2026829228 (frente 2)
790	9	2026-10-16 14:40:47.47913-04	info	Pesquisando contrato: C2026829228
791	9	2026-10-16 14:40:49.046536-04	warning	Contrato C2026829335 não encontrado na busca.
792	9	2026-10-16 14:40:49.046633-04	info	[24/52] Processando C2026828532 (frente 3)
793	9	2026-10-16 14:40:49.04666-04	info	Pesquisando contrato: C2026828532
794	9	2026-10-16 14:40:49.573381-04	warning	Contrato C2026829228 não encontrado na busca.
795	9	2026-10-16 14:40:49.573488-04	info	[25/52] Processando C2026828391 (frente 2)
796	9	2026-10-16 14:40:49.573539-04	info	Pesquisando contrato: C2026828391
797	9	2026-10-16 14:40:51.145541-04	warning	Contrato C2026828532 não encontrado na busca.
798	9	2026-10-16 14:40:51.145653-04	info	[26/52] Processando C2025811697 (frente 3)
799	9	2026-10-16 14:40:51.145709-04	info	Pesquisando contrato: C2025811697
800	9	2026-10-16 14:40:51.669065-04	warning	Contrato C2026828391 não encontrado na busca.
801	9	2026-10-16 14:40:51.669152-04	info	[27/52] Processando C2026827793 (frente 2)
822	9	2026-10-16 14:40:59.994619-04	info	[34/52] Processando C2026827161 (frente 2)
823	9	2026-10-16 14:40:59.994689-04	info	Pesquisando contrato: C2026827161
824	9	2026-10-16 14:41:01.252317-04	warning	Contrato C2026827146 não encontrado na busca.
825	9	2026-10-16 14:41:01.252418-04	info	[35/52] Processando C2026827166 (frente 3)
826	9	2026-10-16 14:41:01.252445-04	info	Pesquisando contrato: C2026827166
827	9	2026-10-16 14:41:02.090768-04	warning	Contrato C2026827161 não encontrado na busca.
828	9	2026-10-16 14:41:02.090875-04	info	[36/52] Processando C2026827151 (frente 2)
829	9	2026-10-16 14:41:02.090897-04	info	Pesquisando contrato: C2026827151
830	9	2026-10-16 14:41:03.359957-04	warning	Contrato C2026827166 não encontrado na busca.
831	9	2026-10-16 14:41:03.360068-04	info	[37/52] Processando C2026826722 (frente 3)
832	9	2026-10-16 14:41:03.36012-04	info	Pesquisando contrato: C2026826722
833	9	2026-10-16 14:41:04.102259-04	warning	Contrato C2026827151 não encontrado na busca.
834	9	2026-10-16 14:41:04.102363-04	info	[38/52] Processando C2026826100 (frente 2)
835	9	2026-10-16 14:41:04.102418-04	info	Pesquisando contrato: C2026826100
836	9	2026-10-16 14:41:05.468905-04	warning	Contrato C2026826722 não encontrado na busca.
837	9	2026-10-16 14:41:05.469007-04	info	[39/52] Processando C2026825492 (frente 3)
838	9	2026-10-16 14:41:05.469053-04	info	Pesquisando contrato: C2026825492
839	9	2026-10-16 14:41:06.20463-04	warning	Contrato C2026826100 não encontrado na busca.
840	9	2026-10-16 14:41:06.204725-04	info	[40/52] Processando C2026825327 (frente 2)
841	9	2026-10-16 14:41:06.204754-04	info	Pesquisando contrato: C2026825327
1290	16	2026-10-16 16:32:24.715966-04	info	[24/52] Processando C2026828532
1311	16	2026-10-16 16:39:55.671694-04	info	C2026827791 coletado em 67.2s
1312	16	2026-10-16 16:39:55.672238-04	info	[29/52] Processando C2026827335
1313	16	2026-10-16 16:39:55.672325-04	info	Pesquisando contrato: C2026827335
1314	16	2026-10-16 16:39:59.111964-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1315	16	2026-10-16 16:41:01.067995-04	info	C2026827335 coletado em 65.4s
1316	16	2026-10-16 16:41:01.068286-04	info	[30/52] Processando C2026827341
1317	16	2026-10-16 16:41:01.06833-04	info	Pesquisando contrato: C2026827341
1318	16	2026-10-16 16:41:04.990365-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1319	16	2026-10-16 16:42:08.308372-04	info	C2026827341 coletado em 67.2s
1320	16	2026-10-16 16:42:08.308845-04	info	[31/52] Processando C2026827349
1321	16	2026-10-16 16:42:08.308923-04	info	Pesquisando contrato: C2026827349
1322	16	2026-10-16 16:42:12.544242-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1323	16	2026-10-16 16:43:18.134983-04	info	C2026827349 coletado em 69.8s
1324	16	2026-10-16 16:43:18.135248-04	info	[32/52] Processando C2026827137
1325	16	2026-10-16 16:43:18.135279-04	info	Pesquisando contrato: C2026827137
1326	16	2026-10-16 16:43:21.182466-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1327	16	2026-10-16 16:44:18.036875-04	info	C2026827137 coletado em 59.9s
1328	16	2026-10-16 16:44:18.037188-04	info	[33/52] Processando C2026827146
1329	16	2026-10-16 16:44:18.037251-04	info	Pesquisando contrato: C2026827146
1330	16	2026-10-16 16:44:20.87206-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1460	18	2026-10-27 15:25:00.289988-04	info	C2026830338 coletado em 67.0s
1461	18	2026-10-27 15:25:00.290252-04	info	[20/45] Processando C2026830326
1462	18	2026-10-27 15:25:00.290297-04	info	Pesquisando contrato: C2026830326
1463	18	2026-10-27 15:25:03.398912-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1464	18	2026-10-27 15:26:08.159243-04	info	C2026830326 coletado em 67.9s
1465	18	2026-10-27 15:26:08.15958-04	info	[21/45] Processando C2026830018
1466	18	2026-10-27 15:26:08.159646-04	info	Pesquisando contrato: C2026830018
1467	18	2026-10-27 15:26:12.271575-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1468	18	2026-10-27 15:27:12.719812-04	info	C2026830018 coletado em 64.6s
1469	18	2026-10-27 15:27:12.720265-04	info	[22/45] Processando C2026830050
1470	18	2026-10-27 15:27:12.720361-04	info	Pesquisando contrato: C2026830050
1471	18	2026-10-27 15:27:19.727883-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1472	18	2026-10-27 15:28:25.706956-04	info	C2026830050 coletado em 73.0s
1473	18	2026-10-27 15:28:25.707211-04	info	[23/45] Processando C2026829737
1474	18	2026-10-27 15:28:25.707267-04	info	Pesquisando contrato: C2026829737
1475	18	2026-10-27 15:28:29.32503-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1476	18	2026-10-27 15:29:31.041787-04	info	C2026829737 coletado em 65.3s
1477	18	2026-10-27 15:29:31.042046-04	info	[24/45] Processando C2026829743
1478	18	2026-10-27 15:29:31.042091-04	info	Pesquisando contrato: C2026829743
1479	18	2026-10-27 15:29:33.756872-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1500	18	2026-10-27 15:36:39.397213-04	info	Pesquisando contrato: C2026828391
1501	18	2026-10-27 15:36:45.545592-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1502	18	2026-10-27 15:38:06.255261-04	info	C2026828391 coletado em 86.9s
1503	18	2026-10-27 15:38:06.255585-04	info	[30/45] Processando C2025811697
1504	18	2026-10-27 15:38:06.25565-04	info	Pesquisando contrato: C2025811697
1505	18	2026-10-27 15:38:16.471374-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1506	18	2026-10-27 15:39:42.098552-04	info	C2025811697 coletado em 95.8s
861	9	2026-10-16 14:41:13.79106-04	info	[47/52] Processando C2026824759 (frente 3)
862	10	2026-10-16 14:41:50.221788-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
863	11	2026-10-16 15:04:57.846428-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
864	11	2026-10-16 15:04:58.818622-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
865	11	2026-10-16 15:04:58.818957-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
866	11	2026-10-16 15:04:59.258899-04	info	1. Acessando página SSO: https://sso.lge.com/
867	11	2026-10-16 15:05:04.560359-04	info	2. Clicando em Self-service OTP (#OTP)...
868	11	2026-10-16 15:05:04.832819-04	info	3. Preenchendo senha e submetendo autenticação (#myButton)...
869	11	2026-10-16 15:05:10.385312-04	info	4. Clicando em OTP temporário (.tempPw)...
870	11	2026-10-16 15:05:11.650928-04	info	5. Tentativa 1/5 de validação do formulário...
871	11	2026-10-16 15:05:13.361364-04	info	Captcha reconhecido: '7nw2g'
872	11	2026-10-16 15:05:13.37756-04	info	Submetendo requisição e aguardando resposta da API...
873	11	2026-10-16 15:05:14.432174-04	info	Resposta do serviço: 0#Temporary password has been sent to your PC outlook e-mail and mobile office on your smart phone. If you don't use either PC outlook e-mail or mobile office, please contact SPoC center(1544-3766/82-1544-3766).#8m825755
874	11	2026-10-16 15:05:14.43229-04	info	OTP obtido com sucesso: 8m825755
875	11	2026-10-16 15:05:14.465914-04	info	OTP temporário obtido para login: 8m825755
876	11	2026-10-16 15:05:14.466049-04	info	Iniciando nova instância do navegador Playwright...
877	11	2026-10-16 15:05:14.756417-04	info	Navegando para o portal de login: https://sso.lge.com/
878	11	2026-10-16 15:05:15.660564-04	info	Preenchendo User ID e Senha corporativa...
879	11	2026-10-16 15:05:19.313398-04	info	Aguardando campo #OTPPASSWORD e preenchendo token...
880	11	2026-10-16 15:05:19.32395-04	info	Clicando no botão de login (#loginSsobtn)...
881	11	2026-10-16 15:05:23.2498-04	info	Navegando para a página do LMS: https://lms.lge.com/#/app/dashboard
882	11	2026-10-16 15:06:45.136425-04	info	Página posicionada com sucesso em: https://lms.lge.com/#/app/dashboard
883	11	2026-10-16 15:06:45.164536-04	info	Navegando para a URL de busca de contratos: https://lms.lge.com/#/app/contract/search
884	11	2026-10-16 15:06:48.166909-04	info	Filtrando por Subsidiary Code: LGESP...
885	11	2026-10-16 15:06:48.333308-04	info	Filtrando por período de data (Request Date): 1...
886	11	2026-10-16 15:06:56.270876-04	info	Iniciando o download do arquivo de exportação de contratos...
887	11	2026-10-16 15:06:56.366785-04	info	Relatório de contratos salvo com sucesso em: /app/downloads/relatorio_contratos.xlsx
888	11	2026-10-16 15:06:56.386444-04	info	Lendo planilha: /app/downloads/relatorio_contratos.xlsx
889	11	2026-10-16 15:06:56.519813-04	info	Linhas após filtro 'mao' em 'Department of the person in charge': 52 de 789
890	11	2026-10-16 15:06:56.522506-04	info	Coletando 52 contratos com 3 frente(s) em paralelo
891	11	2026-10-16 15:06:56.522613-04	info	[1/52] Processando C2026833448 (frente 1)
892	11	2026-10-16 15:06:56.522644-04	info	Pesquisando contrato: C2026833448
893	11	2026-10-16 15:07:01.691724-04	info	[2/52] Processando C2026833165 (frente 2)
894	11	2026-10-16 15:07:05.364253-04	info	Pesquisando contrato: C2026833165
895	11	2026-10-16 15:07:05.369361-04	info	[3/52] Processando C2026833176 (frente 3)
896	11	2026-10-16 15:07:07.451053-04	warning	Contrato C2026833165 não encontrado na busca.
897	11	2026-10-16 15:07:07.472497-04	info	Print da falha de nao_encontrado_C2026833165 salvo em /app/downloads/erros/nao_encontrado_C2026833165.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026833165)
898	11	2026-10-16 15:07:07.472654-04	info	[4/52] Processando C2026832850 (frente 2)
899	11	2026-10-16 15:07:07.472714-04	info	Pesquisando contrato: C2026832850
900	11	2026-10-16 15:07:09.554243-04	warning	Contrato C2026832850 não encontrado na busca.
901	11	2026-10-16 15:07:09.570556-04	info	Print da falha de nao_encontrado_C2026832850 salvo em /app/downloads/erros/nao_encontrado_C2026832850.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026832850)
902	11	2026-10-16 15:07:09.570641-04	info	[5/52] Processando C2026831822 (frente 2)
903	11	2026-10-16 15:07:09.57067-04	info	Pesquisando contrato: C2026831822
904	11	2026-10-16 15:07:11.660378-04	warning	Contrato C2026831822 não encontrado na busca.
905	11	2026-10-16 15:07:11.676181-04	info	Print da falha de nao_encontrado_C2026831822 salvo em /app/downloads/erros/nao_encontrado_C2026831822.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026831822)
906	11	2026-10-16 15:07:11.676261-04	info	[6/52] Processando C2026831823 (frente 2)
907	11	2026-10-16 15:07:11.676289-04	info	Pesquisando contrato: C2026831823
908	11	2026-10-16 15:07:13.766445-04	warning	Contrato C2026831823 não encontrado na busca.
909	11	2026-10-16 15:07:13.786472-04	info	Print da falha de nao_encontrado_C2026831823 salvo em /app/downloads/erros/nao_encontrado_C2026831823.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026831823)
910	11	2026-10-16 15:07:13.786573-04	info	[7/52] Processando C2026831469 (frente 2)
911	11	2026-10-16 15:07:13.786611-04	info	Pesquisando contrato: C2026831469
912	11	2026-10-16 15:07:15.863398-04	warning	Contrato C2026831469 não encontrado na busca.
913	11	2026-10-16 15:07:15.886371-04	info	Print da falha de nao_encontrado_C2026831469 salvo em /app/downloads/erros/nao_encontrado_C2026831469.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026831469)
914	11	2026-10-16 15:07:15.886484-04	info	[8/52] Processando C2026830501 (frente 2)
915	11	2026-10-16 15:07:15.886545-04	info	Pesquisando contrato: C2026830501
916	11	2026-10-16 15:07:17.959864-04	warning	Contrato C2026830501 não encontrado na busca.
917	11	2026-10-16 15:07:17.977352-04	info	Print da falha de nao_encontrado_C2026830501 salvo em /app/downloads/erros/nao_encontrado_C2026830501.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026830501)
918	11	2026-10-16 15:07:17.977469-04	info	[9/52] Processando C2026830541 (frente 2)
919	11	2026-10-16 15:07:17.97752-04	info	Pesquisando contrato: C2026830541
920	11	2026-10-16 15:07:20.052555-04	warning	Contrato C2026830541 não encontrado na busca.
921	11	2026-10-16 15:07:20.068963-04	info	Print da falha de nao_encontrado_C2026830541 salvo em /app/downloads/erros/nao_encontrado_C2026830541.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026830541)
922	11	2026-10-16 15:07:20.069069-04	info	[10/52] Processando C2026830325 (frente 2)
923	11	2026-10-16 15:07:20.069124-04	info	Pesquisando contrato: C2026830325
924	11	2026-10-16 15:07:22.154832-04	warning	Contrato C2026830325 não encontrado na busca.
925	11	2026-10-16 15:07:22.171467-04	info	Print da falha de nao_encontrado_C2026830325 salvo em /app/downloads/erros/nao_encontrado_C2026830325.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026830325)
926	11	2026-10-16 15:07:22.17158-04	info	[11/52] Processando C2026830319 (frente 2)
927	11	2026-10-16 15:07:22.171633-04	info	Pesquisando contrato: C2026830319
928	11	2026-10-16 15:07:24.257245-04	warning	Contrato C2026830319 não encontrado na busca.
1122	12	2026-10-16 15:43:16.944281-04	info	Aguardando campo #OTPPASSWORD e preenchendo token...
929	11	2026-10-16 15:07:24.271962-04	info	Print da falha de nao_encontrado_C2026830319 salvo em /app/downloads/erros/nao_encontrado_C2026830319.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026830319)
930	11	2026-10-16 15:07:24.272045-04	info	[12/52] Processando C2026830310 (frente 2)
931	11	2026-10-16 15:07:24.272076-04	info	Pesquisando contrato: C2026830310
932	11	2026-10-16 15:07:26.335631-04	warning	Contrato C2026830310 não encontrado na busca.
933	11	2026-10-16 15:07:26.352897-04	info	Print da falha de nao_encontrado_C2026830310 salvo em /app/downloads/erros/nao_encontrado_C2026830310.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026830310)
934	11	2026-10-16 15:07:26.353004-04	info	[13/52] Processando C2026830326 (frente 2)
935	11	2026-10-16 15:07:26.353055-04	info	Pesquisando contrato: C2026830326
936	11	2026-10-16 15:07:28.420741-04	warning	Contrato C2026830326 não encontrado na busca.
937	11	2026-10-16 15:07:28.436635-04	info	Print da falha de nao_encontrado_C2026830326 salvo em /app/downloads/erros/nao_encontrado_C2026830326.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026830326)
938	11	2026-10-16 15:07:28.436766-04	info	[14/52] Processando C2026830332 (frente 2)
939	11	2026-10-16 15:07:28.436825-04	info	Pesquisando contrato: C2026830332
940	11	2026-10-16 15:07:30.505722-04	warning	Contrato C2026830332 não encontrado na busca.
941	11	2026-10-16 15:07:30.520827-04	info	Print da falha de nao_encontrado_C2026830332 salvo em /app/downloads/erros/nao_encontrado_C2026830332.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026830332)
942	11	2026-10-16 15:07:30.520981-04	info	[15/52] Processando C2026830338 (frente 2)
943	11	2026-10-16 15:07:30.521048-04	info	Pesquisando contrato: C2026830338
944	11	2026-10-16 15:07:32.602611-04	warning	Contrato C2026830338 não encontrado na busca.
945	11	2026-10-16 15:07:32.632055-04	info	Print da falha de nao_encontrado_C2026830338 salvo em /app/downloads/erros/nao_encontrado_C2026830338.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026830338)
946	11	2026-10-16 15:07:32.632151-04	info	[16/52] Processando C2026830337 (frente 2)
947	11	2026-10-16 15:07:32.632195-04	info	Pesquisando contrato: C2026830337
948	11	2026-10-16 15:07:34.736005-04	warning	Contrato C2026830337 não encontrado na busca.
949	11	2026-10-16 15:07:34.750332-04	info	Print da falha de nao_encontrado_C2026830337 salvo em /app/downloads/erros/nao_encontrado_C2026830337.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026830337)
950	11	2026-10-16 15:07:34.750493-04	info	[17/52] Processando C2026830018 (frente 2)
951	11	2026-10-16 15:07:34.750573-04	info	Pesquisando contrato: C2026830018
952	11	2026-10-16 15:07:36.826084-04	warning	Contrato C2026830018 não encontrado na busca.
953	11	2026-10-16 15:07:36.841883-04	info	Print da falha de nao_encontrado_C2026830018 salvo em /app/downloads/erros/nao_encontrado_C2026830018.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026830018)
954	11	2026-10-16 15:07:36.842017-04	info	[18/52] Processando C2026830050 (frente 2)
955	11	2026-10-16 15:07:36.842048-04	info	Pesquisando contrato: C2026830050
956	11	2026-10-16 15:07:38.917137-04	warning	Contrato C2026830050 não encontrado na busca.
957	11	2026-10-16 15:07:38.930833-04	info	Print da falha de nao_encontrado_C2026830050 salvo em /app/downloads/erros/nao_encontrado_C2026830050.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026830050)
958	11	2026-10-16 15:07:38.930931-04	info	[19/52] Processando C2026829737 (frente 2)
959	11	2026-10-16 15:07:38.930979-04	info	Pesquisando contrato: C2026829737
960	11	2026-10-16 15:07:41.007739-04	warning	Contrato C2026829737 não encontrado na busca.
961	11	2026-10-16 15:07:41.021858-04	info	Print da falha de nao_encontrado_C2026829737 salvo em /app/downloads/erros/nao_encontrado_C2026829737.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026829737)
962	11	2026-10-16 15:07:41.021965-04	info	[20/52] Processando C2026829743 (frente 2)
963	11	2026-10-16 15:07:41.022014-04	info	Pesquisando contrato: C2026829743
964	11	2026-10-16 15:07:43.08907-04	warning	Contrato C2026829743 não encontrado na busca.
965	11	2026-10-16 15:07:43.105064-04	info	Print da falha de nao_encontrado_C2026829743 salvo em /app/downloads/erros/nao_encontrado_C2026829743.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026829743)
966	11	2026-10-16 15:07:43.10516-04	info	[21/52] Processando C2026829481 (frente 2)
967	11	2026-10-16 15:07:43.105212-04	info	Pesquisando contrato: C2026829481
968	11	2026-10-16 15:07:45.202961-04	warning	Contrato C2026829481 não encontrado na busca.
969	11	2026-10-16 15:07:45.217972-04	info	Print da falha de nao_encontrado_C2026829481 salvo em /app/downloads/erros/nao_encontrado_C2026829481.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026829481)
970	11	2026-10-16 15:07:45.218078-04	info	[22/52] Processando C2026829335 (frente 2)
971	11	2026-10-16 15:07:45.21813-04	info	Pesquisando contrato: C2026829335
972	11	2026-10-16 15:07:47.292162-04	warning	Contrato C2026829335 não encontrado na busca.
973	11	2026-10-16 15:07:47.30749-04	info	Print da falha de nao_encontrado_C2026829335 salvo em /app/downloads/erros/nao_encontrado_C2026829335.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026829335)
974	11	2026-10-16 15:07:47.307622-04	info	[23/52] Processando C2026829228 (frente 2)
975	11	2026-10-16 15:07:47.307685-04	info	Pesquisando contrato: C2026829228
976	11	2026-10-16 15:07:49.377319-04	warning	Contrato C2026829228 não encontrado na busca.
977	11	2026-10-16 15:07:49.391507-04	info	Print da falha de nao_encontrado_C2026829228 salvo em /app/downloads/erros/nao_encontrado_C2026829228.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026829228)
978	11	2026-10-16 15:07:49.39161-04	info	[24/52] Processando C2026828532 (frente 2)
979	11	2026-10-16 15:07:49.391658-04	info	Pesquisando contrato: C2026828532
980	11	2026-10-16 15:07:51.465842-04	warning	Contrato C2026828532 não encontrado na busca.
981	11	2026-10-16 15:07:51.481385-04	info	Print da falha de nao_encontrado_C2026828532 salvo em /app/downloads/erros/nao_encontrado_C2026828532.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026828532)
982	11	2026-10-16 15:07:51.481475-04	info	[25/52] Processando C2026828391 (frente 2)
983	11	2026-10-16 15:07:51.481524-04	info	Pesquisando contrato: C2026828391
984	11	2026-10-16 15:07:53.566023-04	warning	Contrato C2026828391 não encontrado na busca.
985	11	2026-10-16 15:07:53.581867-04	info	Print da falha de nao_encontrado_C2026828391 salvo em /app/downloads/erros/nao_encontrado_C2026828391.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026828391)
986	11	2026-10-16 15:07:53.58203-04	info	[26/52] Processando C2025811697 (frente 2)
987	11	2026-10-16 15:07:53.582085-04	info	Pesquisando contrato: C2025811697
988	11	2026-10-16 15:07:55.688646-04	warning	Contrato C2025811697 não encontrado na busca.
989	11	2026-10-16 15:07:55.704409-04	info	Print da falha de nao_encontrado_C2025811697 salvo em /app/downloads/erros/nao_encontrado_C2025811697.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2025811697)
990	11	2026-10-16 15:07:55.704505-04	info	[27/52] Processando C2026827793 (frente 2)
991	11	2026-10-16 15:07:55.704541-04	info	Pesquisando contrato: C2026827793
992	11	2026-10-16 15:07:57.771848-04	warning	Contrato C2026827793 não encontrado na busca.
1123	12	2026-10-16 15:43:16.954048-04	info	Clicando no botão de login (#loginSsobtn)...
993	11	2026-10-16 15:07:57.786621-04	info	Print da falha de nao_encontrado_C2026827793 salvo em /app/downloads/erros/nao_encontrado_C2026827793.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026827793)
994	11	2026-10-16 15:07:57.786707-04	info	[28/52] Processando C2026827791 (frente 2)
995	11	2026-10-16 15:07:57.786736-04	info	Pesquisando contrato: C2026827791
996	11	2026-10-16 15:07:59.863956-04	warning	Contrato C2026827791 não encontrado na busca.
997	11	2026-10-16 15:07:59.879992-04	info	Print da falha de nao_encontrado_C2026827791 salvo em /app/downloads/erros/nao_encontrado_C2026827791.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026827791)
998	11	2026-10-16 15:07:59.880095-04	info	[29/52] Processando C2026827335 (frente 2)
999	11	2026-10-16 15:07:59.880145-04	info	Pesquisando contrato: C2026827335
1000	11	2026-10-16 15:08:01.951633-04	warning	Contrato C2026827335 não encontrado na busca.
1001	11	2026-10-16 15:08:01.966292-04	info	Print da falha de nao_encontrado_C2026827335 salvo em /app/downloads/erros/nao_encontrado_C2026827335.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026827335)
1002	11	2026-10-16 15:08:01.966395-04	info	[30/52] Processando C2026827341 (frente 2)
1003	11	2026-10-16 15:08:01.966444-04	info	Pesquisando contrato: C2026827341
1004	11	2026-10-16 15:08:04.038363-04	warning	Contrato C2026827341 não encontrado na busca.
1005	11	2026-10-16 15:08:04.051908-04	info	Print da falha de nao_encontrado_C2026827341 salvo em /app/downloads/erros/nao_encontrado_C2026827341.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026827341)
1006	11	2026-10-16 15:08:04.052054-04	info	[31/52] Processando C2026827349 (frente 2)
1007	11	2026-10-16 15:08:04.052115-04	info	Pesquisando contrato: C2026827349
1008	11	2026-10-16 15:08:06.141875-04	warning	Contrato C2026827349 não encontrado na busca.
1009	11	2026-10-16 15:08:06.156439-04	info	Print da falha de nao_encontrado_C2026827349 salvo em /app/downloads/erros/nao_encontrado_C2026827349.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026827349)
1010	11	2026-10-16 15:08:06.156563-04	info	[32/52] Processando C2026827137 (frente 2)
1011	11	2026-10-16 15:08:06.156593-04	info	Pesquisando contrato: C2026827137
1012	11	2026-10-16 15:08:08.220809-04	warning	Contrato C2026827137 não encontrado na busca.
1013	11	2026-10-16 15:08:08.236235-04	info	Print da falha de nao_encontrado_C2026827137 salvo em /app/downloads/erros/nao_encontrado_C2026827137.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026827137)
1014	11	2026-10-16 15:08:08.236384-04	info	[33/52] Processando C2026827146 (frente 2)
1015	11	2026-10-16 15:08:08.236453-04	info	Pesquisando contrato: C2026827146
1016	11	2026-10-16 15:08:10.311219-04	warning	Contrato C2026827146 não encontrado na busca.
1017	11	2026-10-16 15:08:10.329509-04	info	Print da falha de nao_encontrado_C2026827146 salvo em /app/downloads/erros/nao_encontrado_C2026827146.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026827146)
1018	11	2026-10-16 15:08:10.329611-04	info	[34/52] Processando C2026827161 (frente 2)
1019	11	2026-10-16 15:08:10.329657-04	info	Pesquisando contrato: C2026827161
1020	11	2026-10-16 15:08:12.403565-04	warning	Contrato C2026827161 não encontrado na busca.
1021	11	2026-10-16 15:08:12.425283-04	info	Print da falha de nao_encontrado_C2026827161 salvo em /app/downloads/erros/nao_encontrado_C2026827161.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026827161)
1022	11	2026-10-16 15:08:12.425379-04	info	[35/52] Processando C2026827166 (frente 2)
1023	11	2026-10-16 15:08:12.425426-04	info	Pesquisando contrato: C2026827166
1024	11	2026-10-16 15:08:14.493068-04	warning	Contrato C2026827166 não encontrado na busca.
1025	11	2026-10-16 15:08:14.511838-04	info	Print da falha de nao_encontrado_C2026827166 salvo em /app/downloads/erros/nao_encontrado_C2026827166.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026827166)
1026	11	2026-10-16 15:08:14.511943-04	info	[36/52] Processando C2026827151 (frente 2)
1027	11	2026-10-16 15:08:14.511997-04	info	Pesquisando contrato: C2026827151
1028	11	2026-10-16 15:08:16.609318-04	warning	Contrato C2026827151 não encontrado na busca.
1029	11	2026-10-16 15:08:16.628935-04	info	Print da falha de nao_encontrado_C2026827151 salvo em /app/downloads/erros/nao_encontrado_C2026827151.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026827151)
1030	11	2026-10-16 15:08:16.629053-04	info	[37/52] Processando C2026826722 (frente 2)
1031	11	2026-10-16 15:08:16.629082-04	info	Pesquisando contrato: C2026826722
1032	11	2026-10-16 15:08:18.707526-04	warning	Contrato C2026826722 não encontrado na busca.
1033	11	2026-10-16 15:08:18.72279-04	info	Print da falha de nao_encontrado_C2026826722 salvo em /app/downloads/erros/nao_encontrado_C2026826722.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026826722)
1034	11	2026-10-16 15:08:18.722864-04	info	[38/52] Processando C2026826100 (frente 2)
1035	11	2026-10-16 15:08:18.722893-04	info	Pesquisando contrato: C2026826100
1036	11	2026-10-16 15:08:20.796493-04	warning	Contrato C2026826100 não encontrado na busca.
1037	11	2026-10-16 15:08:20.812766-04	info	Print da falha de nao_encontrado_C2026826100 salvo em /app/downloads/erros/nao_encontrado_C2026826100.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026826100)
1038	11	2026-10-16 15:08:20.81285-04	info	[39/52] Processando C2026825492 (frente 2)
1039	11	2026-10-16 15:08:20.812874-04	info	Pesquisando contrato: C2026825492
1040	11	2026-10-16 15:08:22.882464-04	warning	Contrato C2026825492 não encontrado na busca.
1041	11	2026-10-16 15:08:22.899742-04	info	Print da falha de nao_encontrado_C2026825492 salvo em /app/downloads/erros/nao_encontrado_C2026825492.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026825492)
1042	11	2026-10-16 15:08:22.899822-04	info	[40/52] Processando C2026825327 (frente 2)
1043	11	2026-10-16 15:08:22.899858-04	info	Pesquisando contrato: C2026825327
1044	11	2026-10-16 15:08:24.97861-04	warning	Contrato C2026825327 não encontrado na busca.
1045	11	2026-10-16 15:08:24.995428-04	info	Print da falha de nao_encontrado_C2026825327 salvo em /app/downloads/erros/nao_encontrado_C2026825327.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026825327)
1046	11	2026-10-16 15:08:24.99553-04	info	[41/52] Processando C2026825339 (frente 2)
1047	11	2026-10-16 15:08:24.99558-04	info	Pesquisando contrato: C2026825339
1048	11	2026-10-16 15:08:27.08083-04	warning	Contrato C2026825339 não encontrado na busca.
1049	11	2026-10-16 15:08:27.096984-04	info	Print da falha de nao_encontrado_C2026825339 salvo em /app/downloads/erros/nao_encontrado_C2026825339.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026825339)
1050	11	2026-10-16 15:08:27.097105-04	info	[42/52] Processando C2026825095 (frente 2)
1051	11	2026-10-16 15:08:27.097159-04	info	Pesquisando contrato: C2026825095
1052	11	2026-10-16 15:08:29.159563-04	warning	Contrato C2026825095 não encontrado na busca.
1053	11	2026-10-16 15:08:29.178649-04	info	Print da falha de nao_encontrado_C2026825095 salvo em /app/downloads/erros/nao_encontrado_C2026825095.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026825095)
1054	11	2026-10-16 15:08:29.178769-04	info	[43/52] Processando C2026825103 (frente 2)
1055	11	2026-10-16 15:08:29.178826-04	info	Pesquisando contrato: C2026825103
1056	11	2026-10-16 15:08:31.244106-04	warning	Contrato C2026825103 não encontrado na busca.
1195	16	2026-10-16 16:02:24.081018-04	info	C2026833448 coletado em 72.5s
1057	11	2026-10-16 15:08:31.262591-04	info	Print da falha de nao_encontrado_C2026825103 salvo em /app/downloads/erros/nao_encontrado_C2026825103.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026825103)
1058	11	2026-10-16 15:08:31.262676-04	info	[44/52] Processando C2026824781 (frente 2)
1059	11	2026-10-16 15:08:31.262702-04	info	Pesquisando contrato: C2026824781
1060	11	2026-10-16 15:08:33.348081-04	warning	Contrato C2026824781 não encontrado na busca.
1061	11	2026-10-16 15:08:33.363174-04	info	Print da falha de nao_encontrado_C2026824781 salvo em /app/downloads/erros/nao_encontrado_C2026824781.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026824781)
1062	11	2026-10-16 15:08:33.3633-04	info	[45/52] Processando C2026824779 (frente 2)
1063	11	2026-10-16 15:08:33.363328-04	info	Pesquisando contrato: C2026824779
1064	11	2026-10-16 15:08:35.43798-04	warning	Tentativa 1/3 de C2026833448 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
1065	11	2026-10-16 15:08:35.443296-04	warning	Contrato C2026824779 não encontrado na busca.
1066	11	2026-10-16 15:08:35.463843-04	info	Print da falha de nao_encontrado_C2026824779 salvo em /app/downloads/erros/nao_encontrado_C2026824779.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026824779)
1067	11	2026-10-16 15:08:35.463967-04	info	[46/52] Processando C2026824756 (frente 2)
1068	11	2026-10-16 15:08:35.484991-04	info	Pesquisando contrato: C2026824756
1069	11	2026-10-16 15:08:37.541639-04	warning	Contrato C2026824756 não encontrado na busca.
1070	11	2026-10-16 15:08:37.562969-04	info	Print da falha de nao_encontrado_C2026824756 salvo em /app/downloads/erros/nao_encontrado_C2026824756.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026824756)
1071	11	2026-10-16 15:08:37.563081-04	info	[47/52] Processando C2026824759 (frente 2)
1072	11	2026-10-16 15:08:37.563107-04	info	Pesquisando contrato: C2026824759
1073	11	2026-10-16 15:08:39.61227-04	warning	Contrato C2026824759 não encontrado na busca.
1074	11	2026-10-16 15:08:39.628307-04	info	Print da falha de nao_encontrado_C2026824759 salvo em /app/downloads/erros/nao_encontrado_C2026824759.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026824759)
1075	11	2026-10-16 15:08:39.628422-04	info	[48/52] Processando C2026824758 (frente 2)
1076	11	2026-10-16 15:08:39.628482-04	info	Pesquisando contrato: C2026824758
1077	11	2026-10-16 15:08:41.679776-04	warning	Contrato C2026824758 não encontrado na busca.
1078	11	2026-10-16 15:08:41.694112-04	info	Print da falha de nao_encontrado_C2026824758 salvo em /app/downloads/erros/nao_encontrado_C2026824758.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026824758)
1079	11	2026-10-16 15:08:41.694226-04	info	[49/52] Processando C2026824655 (frente 2)
1080	11	2026-10-16 15:08:41.694259-04	info	Pesquisando contrato: C2026824655
1081	11	2026-10-16 15:08:43.745714-04	warning	Contrato C2026824655 não encontrado na busca.
1082	11	2026-10-16 15:08:43.76203-04	info	Print da falha de nao_encontrado_C2026824655 salvo em /app/downloads/erros/nao_encontrado_C2026824655.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026824655)
1083	11	2026-10-16 15:08:43.76215-04	info	[50/52] Processando C2026824645 (frente 2)
1084	11	2026-10-16 15:08:43.762185-04	info	Pesquisando contrato: C2026824645
1085	11	2026-10-16 15:08:45.82413-04	warning	Contrato C2026824645 não encontrado na busca.
1086	11	2026-10-16 15:08:45.838959-04	info	Print da falha de nao_encontrado_C2026824645 salvo em /app/downloads/erros/nao_encontrado_C2026824645.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026824645)
1087	11	2026-10-16 15:08:45.839062-04	info	[51/52] Processando C2026824651 (frente 2)
1088	11	2026-10-16 15:08:45.856936-04	info	Pesquisando contrato: C2026824651
1089	11	2026-10-16 15:08:47.914493-04	warning	Contrato C2026824651 não encontrado na busca.
1090	11	2026-10-16 15:08:47.945838-04	info	Print da falha de nao_encontrado_C2026824651 salvo em /app/downloads/erros/nao_encontrado_C2026824651.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026824651)
1091	11	2026-10-16 15:08:47.945947-04	info	[52/52] Processando C2026824660 (frente 2)
1092	11	2026-10-16 15:08:47.945993-04	info	Pesquisando contrato: C2026824660
1093	11	2026-10-16 15:08:50.000516-04	warning	Contrato C2026824660 não encontrado na busca.
1094	11	2026-10-16 15:08:50.014863-04	info	Print da falha de nao_encontrado_C2026824660 salvo em /app/downloads/erros/nao_encontrado_C2026824660.png (tela: https://lms.lge.com/#/app/elastic_search?q=C2026824660)
1095	11	2026-10-16 15:08:50.017195-04	info	Pesquisando contrato: C2026833176
1096	11	2026-10-16 15:08:52.07466-04	warning	Contrato C2026833176 não encontrado na busca.
1097	11	2026-10-16 15:09:07.179363-04	info	Pesquisando contrato: C2026833448
1098	11	2026-10-16 15:10:39.837363-04	warning	Tentativa 2/3 de C2026833448 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
1099	11	2026-10-16 15:10:39.839719-04	info	Pesquisando contrato: C2026833448
1100	11	2026-10-16 15:12:12.498621-04	error	C2026833448 ficou sem dados após 3 tentativas: a tela de detalhe não carregou em 90s
1101	11	2026-10-16 15:12:12.522669-04	info	Print da falha de C2026833448 salvo em /app/downloads/erros/C2026833448.png (tela: https://lms.lge.com/#/app/contract/save?id=978B0286C8A011F19796005056A7DA49)
1102	11	2026-10-16 15:12:12.525383-04	info	52 contratos processados em 316.0s
1103	11	2026-10-16 15:12:12.525442-04	warning	1 contrato(s) sem dados por falha de carregamento: C2026833448
1104	11	2026-10-16 15:12:12.555141-04	info	Planilha consolidada salva em: /app/downloads/contract_review_management.xlsx (52 registros)
1105	11	2026-10-16 15:12:12.57164-04	success	Fluxo concluído com sucesso.
1106	12	2026-10-16 15:42:58.557967-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
1107	12	2026-10-16 15:42:59.60672-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
1108	12	2026-10-16 15:42:59.606962-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
1109	12	2026-10-16 15:43:00.040531-04	info	1. Acessando página SSO: https://sso.lge.com/
1110	12	2026-10-16 15:43:05.179133-04	info	2. Clicando em Self-service OTP (#OTP)...
1111	12	2026-10-16 15:43:05.225094-04	info	3. Preenchendo senha e submetendo autenticação (#myButton)...
1112	12	2026-10-16 15:43:09.200171-04	info	4. Clicando em OTP temporário (.tempPw)...
1113	12	2026-10-16 15:43:10.020784-04	info	5. Tentativa 1/5 de validação do formulário...
1114	12	2026-10-16 15:43:11.218367-04	info	Captcha reconhecido: 'ka6dd'
1115	12	2026-10-16 15:43:11.23277-04	info	Submetendo requisição e aguardando resposta da API...
1116	12	2026-10-16 15:43:11.849103-04	info	Resposta do serviço: 0#Temporary password has been sent to your PC outlook e-mail and mobile office on your smart phone. If you don't use either PC outlook e-mail or mobile office, please contact SPoC center(1544-3766/82-1544-3766).#368x9698
1117	12	2026-10-16 15:43:11.849163-04	info	OTP obtido com sucesso: 368x9698
1118	12	2026-10-16 15:43:11.8791-04	info	OTP temporário obtido para login: 368x9698
1119	12	2026-10-16 15:43:11.879183-04	info	Iniciando nova instância do navegador Playwright...
1120	12	2026-10-16 15:43:12.152288-04	info	Navegando para o portal de login: https://sso.lge.com/
1121	12	2026-10-16 15:43:12.977431-04	info	Preenchendo User ID e Senha corporativa...
1124	12	2026-10-16 15:43:20.994675-04	info	Navegando para a página do LMS: https://lms.lge.com/#/app/dashboard
1125	12	2026-10-16 15:44:43.470427-04	info	Página posicionada com sucesso em: https://lms.lge.com/#/app/dashboard
1126	12	2026-10-16 15:44:43.508416-04	info	Navegando para a URL de busca de contratos: https://lms.lge.com/#/app/contract/search
1127	12	2026-10-16 15:44:46.511029-04	info	Filtrando por Subsidiary Code: LGESP...
1128	12	2026-10-16 15:44:46.684288-04	info	Filtrando por período de data (Request Date): 1...
1129	12	2026-10-16 15:44:59.105602-04	info	Iniciando o download do arquivo de exportação de contratos...
1130	12	2026-10-16 15:44:59.187107-04	info	Relatório de contratos salvo com sucesso em: /app/downloads/relatorio_contratos.xlsx
1131	12	2026-10-16 15:44:59.203802-04	info	Lendo planilha: /app/downloads/relatorio_contratos.xlsx
1132	12	2026-10-16 15:44:59.320121-04	info	Linhas após filtro 'mao' em 'Department of the person in charge': 52 de 789
1133	12	2026-10-16 15:44:59.322037-04	info	Coletando 52 contratos com 3 frente(s) em paralelo (as demais entram depois do primeiro contrato coletado)
1134	12	2026-10-16 15:44:59.322102-04	info	[1/52] Processando C2026833448 (frente 1)
1135	12	2026-10-16 15:44:59.322131-04	info	Pesquisando contrato: C2026833448
1136	12	2026-10-16 15:46:30.80816-04	info	C2026833448 coletado em 91.5s
1137	12	2026-10-16 15:46:30.808276-04	info	[2/52] Processando C2026833165 (frente 1)
1138	12	2026-10-16 15:46:30.808325-04	info	Pesquisando contrato: C2026833165
1139	12	2026-10-16 15:46:48.324936-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1140	12	2026-10-16 15:48:18.827529-04	warning	Tentativa 1/3 de C2026833165 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
1141	12	2026-10-16 15:48:18.830212-04	info	Pesquisando contrato: C2026833165
1142	12	2026-10-16 15:49:57.047782-04	info	Frente 3 pronta
1143	12	2026-10-16 15:49:57.047901-04	info	[3/52] Processando C2026833176 (frente 3)
1144	12	2026-10-16 15:49:57.04795-04	info	Pesquisando contrato: C2026833176
1145	12	2026-10-16 15:50:26.095138-04	info	C2026833165 coletado em 235.3s
1146	12	2026-10-16 15:50:26.095286-04	info	[4/52] Processando C2026832850 (frente 1)
1147	12	2026-10-16 15:50:26.095342-04	info	Pesquisando contrato: C2026832850
1148	12	2026-10-16 15:50:29.89513-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1149	12	2026-10-16 15:51:24.074186-04	info	Frente 2 pronta
1150	12	2026-10-16 15:51:24.07429-04	info	[5/52] Processando C2026831822 (frente 2)
1151	13	2026-10-16 15:57:50.140989-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
1152	13	2026-10-16 15:57:51.074951-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
1153	13	2026-10-16 15:57:51.07529-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
1154	13	2026-10-16 15:57:51.46858-04	info	1. Acessando página SSO: https://sso.lge.com/
1155	13	2026-10-16 15:57:55.729032-04	error	Falha no login do LMS: Page.goto: net::ERR_NAME_NOT_RESOLVED at https://sso.lge.com/\nCall log:\n  - navigating to "https://sso.lge.com/", waiting until "domcontentloaded"\n
1156	14	2026-10-16 15:58:19.588475-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
1157	14	2026-10-16 15:58:20.626641-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
1158	14	2026-10-16 15:58:20.626832-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
1159	14	2026-10-16 15:58:20.958532-04	info	1. Acessando página SSO: https://sso.lge.com/
1160	14	2026-10-16 15:58:21.527513-04	error	Falha no login do LMS: Page.goto: net::ERR_NAME_NOT_RESOLVED at https://sso.lge.com/\nCall log:\n  - navigating to "https://sso.lge.com/", waiting until "domcontentloaded"\n
1161	15	2026-10-16 15:58:25.685092-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
1162	15	2026-10-16 15:58:27.343816-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
1163	15	2026-10-16 15:58:27.344028-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
1164	15	2026-10-16 15:58:27.661184-04	info	1. Acessando página SSO: https://sso.lge.com/
1165	15	2026-10-16 15:58:27.815653-04	error	Falha no login do LMS: Page.goto: net::ERR_NAME_NOT_RESOLVED at https://sso.lge.com/\nCall log:\n  - navigating to "https://sso.lge.com/", waiting until "domcontentloaded"\n
1166	16	2026-10-16 15:59:01.316533-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
1167	16	2026-10-16 15:59:02.763525-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
1168	16	2026-10-16 15:59:02.763744-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
1169	16	2026-10-16 15:59:03.104545-04	info	1. Acessando página SSO: https://sso.lge.com/
1170	16	2026-10-16 15:59:08.541678-04	info	2. Clicando em Self-service OTP (#OTP)...
1171	16	2026-10-16 15:59:08.60414-04	info	3. Preenchendo senha e submetendo autenticação (#myButton)...
1172	16	2026-10-16 15:59:13.82536-04	info	4. Clicando em OTP temporário (.tempPw)...
1173	16	2026-10-16 15:59:15.051723-04	info	5. Tentativa 1/5 de validação do formulário...
1174	16	2026-10-16 15:59:16.743174-04	info	Captcha reconhecido: 'y7wwc'
1175	16	2026-10-16 15:59:16.757425-04	info	Submetendo requisição e aguardando resposta da API...
1176	16	2026-10-16 15:59:17.699113-04	info	Resposta do serviço: 0#Temporary password has been sent to your PC outlook e-mail and mobile office on your smart phone. If you don't use either PC outlook e-mail or mobile office, please contact SPoC center(1544-3766/82-1544-3766).#0621551f
1177	16	2026-10-16 15:59:17.699182-04	info	OTP obtido com sucesso: 0621551f
1178	16	2026-10-16 15:59:17.727007-04	info	OTP temporário obtido para login: 0621551f
1179	16	2026-10-16 15:59:17.727103-04	info	Iniciando nova instância do navegador Playwright...
1180	16	2026-10-16 15:59:17.985641-04	info	Navegando para o portal de login: https://sso.lge.com/
1181	16	2026-10-16 15:59:18.830653-04	info	Preenchendo User ID e Senha corporativa...
1182	16	2026-10-16 15:59:22.992674-04	info	Aguardando campo #OTPPASSWORD e preenchendo token...
1183	16	2026-10-16 15:59:23.000226-04	info	Clicando no botão de login (#loginSsobtn)...
1184	16	2026-10-16 15:59:27.051559-04	info	Navegando para a página do LMS: https://lms.lge.com/#/app/dashboard
1185	16	2026-10-16 16:00:55.255787-04	info	Página posicionada com sucesso em: https://lms.lge.com/#/app/dashboard
1186	16	2026-10-16 16:00:55.288289-04	info	Navegando para a URL de busca de contratos: https://lms.lge.com/#/app/contract/search
1187	16	2026-10-16 16:00:58.290781-04	info	Filtrando por Subsidiary Code: LGESP...
1188	16	2026-10-16 16:00:58.45085-04	info	Filtrando por período de data (Request Date): 1...
1189	16	2026-10-16 16:01:11.401029-04	info	Iniciando o download do arquivo de exportação de contratos...
1190	16	2026-10-16 16:01:11.478266-04	info	Relatório de contratos salvo com sucesso em: /app/downloads/relatorio_contratos.xlsx
1191	16	2026-10-16 16:01:11.497793-04	info	Lendo planilha: /app/downloads/relatorio_contratos.xlsx
1192	16	2026-10-16 16:01:11.613843-04	info	Linhas após filtro 'mao' em 'Department of the person in charge': 52 de 789
1193	16	2026-10-16 16:01:11.614662-04	info	[1/52] Processando C2026833448
1194	16	2026-10-16 16:01:11.614716-04	info	Pesquisando contrato: C2026833448
1196	16	2026-10-16 16:02:24.081428-04	info	[2/52] Processando C2026833165
1197	16	2026-10-16 16:02:24.081497-04	info	Pesquisando contrato: C2026833165
1198	16	2026-10-16 16:02:41.438632-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1199	16	2026-10-16 16:04:05.592549-04	info	C2026833165 coletado em 101.5s
1200	16	2026-10-16 16:04:05.59287-04	info	[3/52] Processando C2026833176
1201	16	2026-10-16 16:04:05.592936-04	info	Pesquisando contrato: C2026833176
1202	16	2026-10-16 16:04:08.912197-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1203	16	2026-10-16 16:04:59.299755-04	info	C2026833176 coletado em 53.7s
1204	16	2026-10-16 16:04:59.300029-04	info	[4/52] Processando C2026832850
1205	16	2026-10-16 16:04:59.300081-04	info	Pesquisando contrato: C2026832850
1206	16	2026-10-16 16:05:02.327385-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1207	16	2026-10-16 16:05:59.617381-04	info	C2026832850 coletado em 60.3s
1208	16	2026-10-16 16:05:59.617898-04	info	[5/52] Processando C2026831822
1209	16	2026-10-16 16:05:59.617972-04	info	Pesquisando contrato: C2026831822
1210	16	2026-10-16 16:06:03.44795-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1291	16	2026-10-16 16:32:24.73544-04	info	Pesquisando contrato: C2026828532
1292	16	2026-10-16 16:32:29.086967-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1293	16	2026-10-16 16:33:25.939754-04	info	C2026828532 coletado em 61.2s
1294	16	2026-10-16 16:33:25.940072-04	info	[25/52] Processando C2026828391
1295	16	2026-10-16 16:33:25.940126-04	info	Pesquisando contrato: C2026828391
1296	16	2026-10-16 16:33:31.618906-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1297	16	2026-10-16 16:34:49.614333-04	info	C2026828391 coletado em 83.7s
1298	16	2026-10-16 16:34:49.614677-04	info	[26/52] Processando C2025811697
1299	16	2026-10-16 16:34:49.614727-04	info	Pesquisando contrato: C2025811697
1300	16	2026-10-16 16:35:05.876469-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1301	16	2026-10-16 16:36:36.287608-04	warning	Tentativa 1/3 de C2025811697 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
1302	16	2026-10-16 16:36:36.293018-04	info	Pesquisando contrato: C2025811697
1303	16	2026-10-16 16:37:44.769857-04	info	C2025811697 coletado em 175.2s
1304	16	2026-10-16 16:37:44.770212-04	info	[27/52] Processando C2026827793
1305	16	2026-10-16 16:37:44.770278-04	info	Pesquisando contrato: C2026827793
1306	16	2026-10-16 16:37:48.690253-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1307	16	2026-10-16 16:38:48.496727-04	info	C2026827793 coletado em 63.7s
1308	16	2026-10-16 16:38:48.497199-04	info	[28/52] Processando C2026827791
1309	16	2026-10-16 16:38:48.497281-04	info	Pesquisando contrato: C2026827791
1310	16	2026-10-16 16:38:51.728896-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1331	16	2026-10-16 16:45:20.198229-04	info	C2026827146 coletado em 62.2s
1332	16	2026-10-16 16:45:20.198543-04	info	[34/52] Processando C2026827161
1333	16	2026-10-16 16:45:20.198601-04	info	Pesquisando contrato: C2026827161
1334	16	2026-10-16 16:45:24.341857-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1335	16	2026-10-16 16:46:19.284421-04	info	C2026827161 coletado em 59.1s
1336	16	2026-10-16 16:46:19.284747-04	info	[35/52] Processando C2026827166
1337	16	2026-10-16 16:46:19.284811-04	info	Pesquisando contrato: C2026827166
1338	16	2026-10-16 16:46:22.514994-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1339	16	2026-10-16 16:47:18.869494-04	info	C2026827166 coletado em 59.6s
1340	16	2026-10-16 16:47:18.8699-04	info	[36/52] Processando C2026827151
1341	16	2026-10-16 16:47:18.869968-04	info	Pesquisando contrato: C2026827151
1342	16	2026-10-16 16:47:22.51665-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1343	16	2026-10-16 16:48:17.557638-04	info	C2026827151 coletado em 58.7s
1344	16	2026-10-16 16:48:17.55799-04	info	[37/52] Processando C2026826722
1345	16	2026-10-16 16:48:17.558068-04	info	Pesquisando contrato: C2026826722
1346	16	2026-10-16 16:48:20.09388-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1347	16	2026-10-16 16:49:17.966966-04	info	C2026826722 coletado em 60.4s
1348	16	2026-10-16 16:49:17.967267-04	info	[38/52] Processando C2026826100
1349	16	2026-10-16 16:49:17.967328-04	info	Pesquisando contrato: C2026826100
1350	16	2026-10-16 16:49:21.71236-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1351	17	2026-10-22 15:08:22.619111-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
1352	17	2026-10-22 15:08:22.619387-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
1353	17	2026-10-22 15:08:23.39861-04	info	1. Acessando página SSO: https://sso.lge.com/
1354	17	2026-10-22 15:08:24.927396-04	error	Falha no login do LMS: Page.goto: net::ERR_NAME_NOT_RESOLVED at https://sso.lge.com/\nCall log:\n  - navigating to "https://sso.lge.com/", waiting until "domcontentloaded"\n
1355	18	2026-10-27 14:58:57.974149-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
1356	18	2026-10-27 14:58:59.306559-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
1357	18	2026-10-27 14:58:59.306806-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
1358	18	2026-10-27 14:58:59.750331-04	info	1. Acessando página SSO: https://sso.lge.com/
1359	18	2026-10-27 14:59:06.935683-04	info	2. Clicando em Self-service OTP (#OTP)...
1360	18	2026-10-27 14:59:06.989235-04	info	3. Preenchendo senha e submetendo autenticação (#myButton)...
1361	18	2026-10-27 14:59:14.36622-04	info	4. Clicando em OTP temporário (.tempPw)...
1362	18	2026-10-27 14:59:15.210078-04	info	5. Tentativa 1/5 de validação do formulário...
1363	18	2026-10-27 14:59:17.298363-04	info	Captcha reconhecido: 'd8r8g'
1364	18	2026-10-27 14:59:17.314361-04	info	Submetendo requisição e aguardando resposta da API...
1365	18	2026-10-27 14:59:17.832103-04	info	Resposta do serviço: 0#Temporary password has been sent to your PC outlook e-mail and mobile office on your smart phone. If you don't use either PC outlook e-mail or mobile office, please contact SPoC center(1544-3766/82-1544-3766).#31957x36
1366	18	2026-10-27 14:59:17.832169-04	info	OTP obtido com sucesso: 31957x36
1367	18	2026-10-27 14:59:17.860022-04	info	OTP temporário obtido para login: 31957x36
1368	18	2026-10-27 14:59:17.86013-04	info	Iniciando nova instância do navegador Playwright...
1369	18	2026-10-27 14:59:18.142441-04	info	Navegando para o portal de login: https://sso.lge.com/
1370	18	2026-10-27 14:59:18.963749-04	info	Preenchendo User ID e Senha corporativa...
1371	18	2026-10-27 14:59:23.538884-04	info	Aguardando campo #OTPPASSWORD e preenchendo token...
1372	18	2026-10-27 14:59:23.72397-04	info	Clicando no botão de login (#loginSsobtn)...
1373	18	2026-10-27 14:59:27.529219-04	info	Navegando para a página do LMS: https://lms.lge.com/#/app/dashboard
1374	18	2026-10-27 15:01:35.948297-04	info	Página posicionada com sucesso em: https://lms.lge.com/#/app/dashboard
1375	18	2026-10-27 15:01:35.973055-04	info	Navegando para a URL de busca de contratos: https://lms.lge.com/#/app/contract/search
1211	16	2026-10-16 16:06:56.290241-04	info	C2026831822 coletado em 56.7s
1212	16	2026-10-16 16:06:56.290746-04	info	[6/52] Processando C2026831823
1213	16	2026-10-16 16:06:56.290815-04	info	Pesquisando contrato: C2026831823
1214	16	2026-10-16 16:07:00.170679-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1215	16	2026-10-16 16:08:07.510987-04	info	C2026831823 coletado em 71.2s
1216	16	2026-10-16 16:08:07.511237-04	info	[7/52] Processando C2026831469
1217	16	2026-10-16 16:08:07.51128-04	info	Pesquisando contrato: C2026831469
1218	16	2026-10-16 16:08:10.428924-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1219	16	2026-10-16 16:09:10.278479-04	info	C2026831469 coletado em 62.8s
1220	16	2026-10-16 16:09:10.278846-04	info	[8/52] Processando C2026830501
1221	16	2026-10-16 16:09:10.278913-04	info	Pesquisando contrato: C2026830501
1222	16	2026-10-16 16:09:13.90142-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1223	16	2026-10-16 16:10:44.366538-04	warning	Tentativa 1/3 de C2026830501 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
1224	16	2026-10-16 16:10:44.371397-04	info	Pesquisando contrato: C2026830501
1225	16	2026-10-16 16:12:21.184971-04	warning	Tentativa 2/3 de C2026830501 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
1226	16	2026-10-16 16:12:21.186872-04	info	Pesquisando contrato: C2026830501
1227	16	2026-10-16 16:13:25.779827-04	info	C2026830501 coletado em 255.5s
1228	16	2026-10-16 16:13:25.780144-04	info	[9/52] Processando C2026830541
1229	16	2026-10-16 16:13:25.780206-04	info	Pesquisando contrato: C2026830541
1230	16	2026-10-16 16:13:34.662494-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1376	18	2026-10-27 15:01:38.975904-04	info	Filtrando por Subsidiary Code: LGESP...
1377	18	2026-10-27 15:01:39.135929-04	info	Filtrando por período de data (Request Date): 1...
1378	18	2026-10-27 15:01:49.077778-04	info	Iniciando o download do arquivo de exportação de contratos...
1379	18	2026-10-27 15:01:49.174349-04	info	Relatório de contratos salvo com sucesso em: /app/downloads/relatorio_contratos.xlsx
1400	18	2026-10-27 15:08:57.989081-04	info	Pesquisando contrato: C2026833448
1401	18	2026-10-27 15:09:00.720423-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1402	18	2026-10-27 15:10:01.989642-04	info	C2026833448 coletado em 64.0s
1403	18	2026-10-27 15:10:01.990013-04	info	[6/45] Processando C2026833165
1404	18	2026-10-27 15:10:01.990067-04	info	Pesquisando contrato: C2026833165
1405	18	2026-10-27 15:10:06.764852-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1406	18	2026-10-27 15:10:58.588814-04	info	C2026833165 coletado em 56.6s
1407	18	2026-10-27 15:10:58.589141-04	info	[7/45] Processando C2026833176
1408	18	2026-10-27 15:10:58.58921-04	info	Pesquisando contrato: C2026833176
1409	18	2026-10-27 15:11:05.226563-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1410	18	2026-10-27 15:11:52.365207-04	info	C2026833176 coletado em 53.8s
1411	18	2026-10-27 15:11:52.365466-04	info	[8/45] Processando C2026832850
1412	18	2026-10-27 15:11:52.365521-04	info	Pesquisando contrato: C2026832850
1413	18	2026-10-27 15:11:54.886032-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1414	18	2026-10-27 15:12:49.455458-04	info	C2026832850 coletado em 57.1s
1415	18	2026-10-27 15:12:49.455825-04	info	[9/45] Processando C2026831822
1416	18	2026-10-27 15:12:49.455898-04	info	Pesquisando contrato: C2026831822
1417	18	2026-10-27 15:12:52.777032-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1418	18	2026-10-27 15:13:36.184625-04	info	C2026831822 coletado em 46.7s
1419	18	2026-10-27 15:13:36.184875-04	info	[10/45] Processando C2026831823
1420	18	2026-10-27 15:13:36.201713-04	info	Pesquisando contrato: C2026831823
1421	18	2026-10-27 15:13:45.868897-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1422	18	2026-10-27 15:14:43.631665-04	info	C2026831823 coletado em 67.4s
1423	18	2026-10-27 15:14:43.63203-04	info	[11/45] Processando C2026831469
1424	18	2026-10-27 15:14:43.632097-04	info	Pesquisando contrato: C2026831469
1425	18	2026-10-27 15:14:46.881867-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1426	18	2026-10-27 15:15:39.46078-04	info	C2026831469 coletado em 55.8s
1427	18	2026-10-27 15:15:39.461071-04	info	[12/45] Processando C2026830501
1428	18	2026-10-27 15:15:39.461126-04	info	Pesquisando contrato: C2026830501
1429	18	2026-10-27 15:15:42.379932-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1430	18	2026-10-27 15:16:17.436237-04	info	C2026830501 coletado em 38.0s
1431	18	2026-10-27 15:16:17.436507-04	info	[13/45] Processando C2026830541
1432	18	2026-10-27 15:16:17.436579-04	info	Pesquisando contrato: C2026830541
1433	18	2026-10-27 15:16:22.251883-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1434	18	2026-10-27 15:17:30.832813-04	warning	Tela de detalhe ainda carregando após 15s; seguindo com o que já carregou. Requisições pendentes: https://lms.lge.com/api/invoice/selectCostBizLawFirmList
1435	18	2026-10-27 15:17:30.868706-04	info	C2026830541 coletado em 73.4s
1436	18	2026-10-27 15:17:30.869084-04	info	[14/45] Processando C2026830325
1437	18	2026-10-27 15:17:30.86914-04	info	Pesquisando contrato: C2026830325
1438	18	2026-10-27 15:19:01.311965-04	warning	Tentativa 1/3 de C2026830325 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
1439	18	2026-10-27 15:19:01.317179-04	info	Pesquisando contrato: C2026830325
1480	18	2026-10-27 15:30:31.139755-04	info	C2026829743 coletado em 60.1s
1481	18	2026-10-27 15:30:31.1401-04	info	[25/45] Processando C2026829481
1482	18	2026-10-27 15:30:31.140173-04	info	Pesquisando contrato: C2026829481
1483	18	2026-10-27 15:30:35.609207-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1484	18	2026-10-27 15:31:40.93005-04	info	C2026829481 coletado em 69.8s
1485	18	2026-10-27 15:31:40.930343-04	info	[26/45] Processando C2026829335
1486	18	2026-10-27 15:31:40.930403-04	info	Pesquisando contrato: C2026829335
1487	18	2026-10-27 15:31:43.717139-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1488	18	2026-10-27 15:32:47.732831-04	info	C2026829335 coletado em 66.8s
1489	18	2026-10-27 15:32:47.733106-04	info	[27/45] Processando C2026829228
1490	18	2026-10-27 15:32:47.733148-04	info	Pesquisando contrato: C2026829228
1491	18	2026-10-27 15:32:50.022839-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1492	18	2026-10-27 15:33:46.169278-04	warning	Tela de detalhe ainda carregando após 15s; seguindo com o que já carregou. Requisições pendentes: https://lms.lge.com/api/invoice/selectCostBizLawFirmList
1493	18	2026-10-27 15:33:46.185611-04	info	C2026829228 coletado em 58.5s
1494	18	2026-10-27 15:33:46.18594-04	info	[28/45] Processando C2026828532
1495	18	2026-10-27 15:33:46.186008-04	info	Pesquisando contrato: C2026828532
1496	18	2026-10-27 15:35:16.711628-04	warning	Tentativa 1/3 de C2026828532 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
1507	18	2026-10-27 15:39:42.098825-04	info	[31/45] Processando C2026827793
1508	18	2026-10-27 15:39:42.098872-04	info	Pesquisando contrato: C2026827793
1509	18	2026-10-27 15:39:45.939032-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1510	18	2026-10-27 15:41:05.641605-04	info	C2026827793 coletado em 83.5s
1511	18	2026-10-27 15:41:05.641832-04	info	[32/45] Processando C2026827791
1512	18	2026-10-27 15:41:05.64188-04	info	Pesquisando contrato: C2026827791
1513	18	2026-10-27 15:41:08.040305-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1514	18	2026-10-27 15:42:11.855159-04	info	C2026827791 coletado em 66.2s
1515	18	2026-10-27 15:42:11.855383-04	info	[33/45] Processando C2026827335
1516	18	2026-10-27 15:42:11.855423-04	info	Pesquisando contrato: C2026827335
1517	18	2026-10-27 15:42:15.378584-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1518	18	2026-10-27 15:43:18.972633-04	info	C2026827335 coletado em 67.1s
1519	18	2026-10-27 15:43:18.972902-04	info	[34/45] Processando C2026827341
1569	18	2026-10-27 15:56:54.856765-04	info	Base Ideal tratada: 45 contrato(s) em /app/downloads/base_ideal.xlsx
1570	18	2026-10-27 15:56:54.893731-04	info	45 contrato(s) gravados no banco: 45 novos, 0 atualizados
1520	18	2026-10-27 15:43:18.991053-04	info	Pesquisando contrato: C2026827341
1521	18	2026-10-27 15:43:24.109565-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1522	18	2026-10-27 15:44:30.581623-04	info	C2026827341 coletado em 71.6s
1523	18	2026-10-27 15:44:30.581853-04	info	[35/45] Processando C2026827349
1524	18	2026-10-27 15:44:30.581894-04	info	Pesquisando contrato: C2026827349
1525	18	2026-10-27 15:44:34.51348-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1526	18	2026-10-27 15:45:42.132369-04	info	C2026827349 coletado em 71.6s
1527	18	2026-10-27 15:45:42.132684-04	info	[36/45] Processando C2026827151
1528	18	2026-10-27 15:45:42.132745-04	info	Pesquisando contrato: C2026827151
1529	18	2026-10-27 15:45:45.878381-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1530	18	2026-10-27 15:46:38.545794-04	info	C2026827151 coletado em 56.4s
1531	18	2026-10-27 15:46:38.546135-04	info	[37/45] Processando C2026827137
1532	18	2026-10-27 15:46:38.54619-04	info	Pesquisando contrato: C2026827137
1533	18	2026-10-27 15:46:41.372677-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1534	18	2026-10-27 15:47:37.409146-04	info	C2026827137 coletado em 58.9s
1535	18	2026-10-27 15:47:37.409455-04	info	[38/45] Processando C2026827146
1536	18	2026-10-27 15:47:37.409522-04	info	Pesquisando contrato: C2026827146
1537	18	2026-10-27 15:47:40.329638-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1538	18	2026-10-27 15:48:50.235662-04	info	C2026827146 coletado em 72.8s
1539	18	2026-10-27 15:48:50.235901-04	info	[39/45] Processando C2026827161
1540	18	2026-10-27 15:48:50.254072-04	info	Pesquisando contrato: C2026827161
1541	18	2026-10-27 15:48:54.922872-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1542	18	2026-10-27 15:49:56.683547-04	info	C2026827161 coletado em 66.4s
1543	18	2026-10-27 15:49:56.683871-04	info	[40/45] Processando C2026827166
1544	18	2026-10-27 15:49:56.683937-04	info	Pesquisando contrato: C2026827166
1545	18	2026-10-27 15:49:59.818382-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1546	18	2026-10-27 15:50:55.58654-04	info	C2026827166 coletado em 58.9s
1547	18	2026-10-27 15:50:55.586996-04	info	[41/45] Processando C2026826722
1548	18	2026-10-27 15:50:55.587059-04	info	Pesquisando contrato: C2026826722
1549	18	2026-10-27 15:50:58.10138-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1550	18	2026-10-27 15:51:49.732601-04	info	C2026826722 coletado em 54.1s
1551	18	2026-10-27 15:51:49.732902-04	info	[42/45] Processando C2026826100
1552	18	2026-10-27 15:51:49.732964-04	info	Pesquisando contrato: C2026826100
1553	18	2026-10-27 15:51:53.989584-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1554	18	2026-10-27 15:53:06.315023-04	info	C2026826100 coletado em 76.6s
1555	18	2026-10-27 15:53:06.315339-04	info	[43/45] Processando C2026825492
1556	18	2026-10-27 15:53:06.315414-04	info	Pesquisando contrato: C2026825492
1557	18	2026-10-27 15:53:18.749758-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1558	18	2026-10-27 15:54:31.109165-04	info	C2026825492 coletado em 84.8s
1559	18	2026-10-27 15:54:31.109392-04	info	[44/45] Processando C2026825327
1560	18	2026-10-27 15:54:31.126608-04	info	Pesquisando contrato: C2026825327
1561	18	2026-10-27 15:54:36.608823-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1562	18	2026-10-27 15:55:40.418628-04	info	C2026825327 coletado em 69.3s
1563	18	2026-10-27 15:55:40.419004-04	info	[45/45] Processando C2026825339
1564	18	2026-10-27 15:55:40.419063-04	info	Pesquisando contrato: C2026825339
1565	18	2026-10-27 15:55:45.038072-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1566	18	2026-10-27 15:56:54.757902-04	info	C2026825339 coletado em 74.3s
1567	18	2026-10-27 15:56:54.771266-04	info	45 contratos processados em 3305.5s
1568	18	2026-10-27 15:56:54.797695-04	info	Planilha consolidada salva em: /app/downloads/contract_review_management.xlsx (45 registros)
1571	18	2026-10-27 15:56:54.907229-04	success	Fluxo concluído com sucesso.
1572	19	2026-10-27 16:08:45.165499-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
1573	20	2026-10-27 16:10:45.644672-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
1574	20	2026-10-27 16:10:46.730676-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
1575	20	2026-10-27 16:10:46.731059-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
1576	20	2026-10-27 16:10:47.117744-04	info	1. Acessando página SSO: https://sso.lge.com/
1577	20	2026-10-27 16:10:52.319744-04	info	2. Clicando em Self-service OTP (#OTP)...
1578	20	2026-10-27 16:10:52.381685-04	info	3. Preenchendo senha e submetendo autenticação (#myButton)...
1579	20	2026-10-27 16:10:56.359463-04	info	4. Clicando em OTP temporário (.tempPw)...
1580	20	2026-10-27 16:10:57.299223-04	info	5. Tentativa 1/5 de validação do formulário...
1581	20	2026-10-27 16:10:58.575864-04	info	Captcha reconhecido: '8nrxa'
1582	20	2026-10-27 16:10:58.589417-04	info	Submetendo requisição e aguardando resposta da API...
1583	20	2026-10-27 16:10:59.208636-04	info	Resposta do serviço: 0#Temporary password has been sent to your PC outlook e-mail and mobile office on your smart phone. If you don't use either PC outlook e-mail or mobile office, please contact SPoC center(1544-3766/82-1544-3766).#89e05155
1584	20	2026-10-27 16:10:59.208733-04	info	OTP obtido com sucesso: 89e05155
1585	20	2026-10-27 16:10:59.237725-04	info	OTP temporário obtido para login: 89e05155
1586	20	2026-10-27 16:10:59.237854-04	info	Iniciando nova instância do navegador Playwright...
1587	20	2026-10-27 16:10:59.502496-04	info	Navegando para o portal de login: https://sso.lge.com/
1588	20	2026-10-27 16:11:00.338439-04	info	Preenchendo User ID e Senha corporativa...
1589	20	2026-10-27 16:11:04.395234-04	info	Aguardando campo #OTPPASSWORD e preenchendo token...
1590	20	2026-10-27 16:11:04.403221-04	info	Clicando no botão de login (#loginSsobtn)...
1591	20	2026-10-27 16:11:08.354944-04	info	Navegando para a página do LMS: https://lms.lge.com/#/app/dashboard
1592	20	2026-10-27 16:12:30.20516-04	info	Página posicionada com sucesso em: https://lms.lge.com/#/app/dashboard
1593	20	2026-10-27 16:12:30.235363-04	info	Navegando para a URL de busca de contratos: https://lms.lge.com/#/app/contract/search
1594	20	2026-10-27 16:12:33.239055-04	info	Filtrando por Subsidiary Code: LGESP...
1595	20	2026-10-27 16:12:33.39184-04	info	Filtrando por período de data (Request Date): 1...
1596	20	2026-10-27 16:12:43.297191-04	info	Iniciando o download do arquivo de exportação de contratos...
1597	20	2026-10-27 16:12:43.377977-04	info	Relatório de contratos salvo com sucesso em: /app/downloads/relatorio_contratos.xlsx
1598	20	2026-10-27 16:12:43.402724-04	info	Lendo planilha: /app/downloads/relatorio_contratos.xlsx
1599	20	2026-10-27 16:12:43.472541-04	info	Linhas após filtro 'mao' em 'Department of the person in charge': 46 de 770
1600	20	2026-10-27 16:12:43.485762-04	info	[1/46] Processando C2026834653
1601	20	2026-10-27 16:12:43.4864-04	info	Pesquisando contrato: C2026834653
1602	20	2026-10-27 16:12:47.196983-04	warning	Contrato C2026834653 não encontrado na busca.
1603	20	2026-10-27 16:12:47.197519-04	info	[2/46] C2026834490 sem mudança de status ('Legal Review in Progress'); reaproveitando dados do banco.
1604	20	2026-10-27 16:12:47.197761-04	info	[3/46] C2026834516 sem mudança de status ('Legal Review in Progress'); reaproveitando dados do banco.
1605	20	2026-10-27 16:12:47.197897-04	info	[4/46] C2026834065 sem mudança de status ('Review Completed'); reaproveitando dados do banco.
1606	20	2026-10-27 16:12:47.198028-04	info	[5/46] C2026833919 sem mudança de status ('Review Completed'); reaproveitando dados do banco.
1607	20	2026-10-27 16:12:47.198149-04	info	[6/46] C2026833448 sem mudança de status ('Legal Comments Provided'); reaproveitando dados do banco.
1608	20	2026-10-27 16:12:47.198268-04	info	[7/46] C2026833165 sem mudança de status ('Review Completed'); reaproveitando dados do banco.
1609	20	2026-10-27 16:12:47.198384-04	info	[8/46] C2026833176 sem mudança de status ('Legal Team Consent in Progress'); reaproveitando dados do banco.
1610	20	2026-10-27 16:12:47.198497-04	info	[9/46] C2026832850 sem mudança de status ('Review Completed'); reaproveitando dados do banco.
1611	20	2026-10-27 16:12:47.198601-04	info	[10/46] C2026831822 sem mudança de status ('Effective Contract'); reaproveitando dados do banco.
1612	20	2026-10-27 16:12:47.198681-04	info	[11/46] Processando C2026831823
1613	20	2026-10-27 16:12:47.198711-04	info	Pesquisando contrato: C2026831823
1614	20	2026-10-27 16:14:21.96304-04	info	C2026831823 coletado em 94.8s
1615	20	2026-10-27 16:14:21.963391-04	info	[12/46] C2026831469 sem mudança de status ('Review Completed'); reaproveitando dados do banco.
1616	20	2026-10-27 16:14:21.963536-04	info	[13/46] C2026830501 sem mudança de status ('Approval Completed'); reaproveitando dados do banco.
1617	20	2026-10-27 16:14:21.963627-04	info	[14/46] C2026830541 sem mudança de status ('Approval Completed'); reaproveitando dados do banco.
1662	20	2026-10-27 16:20:34.205292-04	info	Base Ideal tratada: 46 contrato(s) em /app/downloads/base_ideal.xlsx
1663	20	2026-10-27 16:20:34.242711-04	info	45 contrato(s) gravados no banco: 0 novos, 45 atualizados
1618	20	2026-10-27 16:14:21.98055-04	info	[15/46] C2026830325 sem mudança de status ('Approval Completed'); reaproveitando dados do banco.
1619	20	2026-10-27 16:14:21.980796-04	info	[16/46] C2026830332 sem mudança de status ('Effective Contract'); reaproveitando dados do banco.
1620	20	2026-10-27 16:14:21.980936-04	info	[17/46] C2026830319 sem mudança de status ('Effective Contract'); reaproveitando dados do banco.
1621	20	2026-10-27 16:14:21.981041-04	info	[18/46] C2026830310 sem mudança de status ('Effective Contract'); reaproveitando dados do banco.
1622	20	2026-10-27 16:14:21.981129-04	info	[19/46] C2026830337 sem mudança de status ('Approval Completed'); reaproveitando dados do banco.
1623	20	2026-10-27 16:14:21.981222-04	info	[20/46] C2026830338 sem mudança de status ('Review Completed'); reaproveitando dados do banco.
1624	20	2026-10-27 16:14:21.981298-04	info	[21/46] C2026830326 sem mudança de status ('Effective Contract'); reaproveitando dados do banco.
1625	20	2026-10-27 16:14:21.981371-04	info	[22/46] C2026830018 sem mudança de status ('Approval Completed'); reaproveitando dados do banco.
1626	20	2026-10-27 16:14:21.981444-04	info	[23/46] C2026830050 sem mudança de status ('Effective Contract'); reaproveitando dados do banco.
1627	20	2026-10-27 16:14:21.981527-04	info	[24/46] C2026829737 sem mudança de status ('Legal Team Consent Completed'); reaproveitando dados do banco.
1628	20	2026-10-27 16:14:21.981611-04	info	[25/46] C2026829743 sem mudança de status ('Review Completed'); reaproveitando dados do banco.
1629	20	2026-10-27 16:14:21.981685-04	info	[26/46] C2026829481 sem mudança de status ('Effective Contract'); reaproveitando dados do banco.
1630	20	2026-10-27 16:14:21.98176-04	info	[27/46] C2026829335 sem mudança de status ('Legal Team Consent Completed'); reaproveitando dados do banco.
1631	20	2026-10-27 16:14:21.981831-04	info	[28/46] C2026829228 sem mudança de status ('Effective Contract'); reaproveitando dados do banco.
1632	20	2026-10-27 16:14:21.981901-04	info	[29/46] C2026828532 sem mudança de status ('Effective Contract'); reaproveitando dados do banco.
1633	20	2026-10-27 16:14:21.981966-04	info	[30/46] C2026828391 sem mudança de status ('Approval Completed'); reaproveitando dados do banco.
1634	20	2026-10-27 16:14:21.982026-04	info	[31/46] Processando C2025811697
1635	20	2026-10-27 16:14:21.982049-04	info	Pesquisando contrato: C2025811697
1636	20	2026-10-27 16:14:35.303755-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1637	20	2026-10-27 16:16:05.706085-04	warning	Tentativa 1/3 de C2025811697 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
1638	20	2026-10-27 16:16:05.726341-04	info	Pesquisando contrato: C2025811697
1639	20	2026-10-27 16:17:38.349085-04	warning	Tentativa 2/3 de C2025811697 falhou (a tela de detalhe não carregou em 90s). Tentando de novo com a aba de detalhe reaberta.
1640	20	2026-10-27 16:17:38.351406-04	info	Pesquisando contrato: C2025811697
1641	20	2026-10-27 16:19:10.647986-04	info	C2025811697 coletado em 288.7s
1642	20	2026-10-27 16:19:10.648348-04	info	[32/46] C2026827793 sem mudança de status ('Biz-Drop'); reaproveitando dados do banco.
1643	20	2026-10-27 16:19:10.648563-04	info	[33/46] C2026827791 sem mudança de status ('Biz-Drop'); reaproveitando dados do banco.
1644	20	2026-10-27 16:19:10.648756-04	info	[34/46] C2026827335 sem mudança de status ('Contract Expired'); reaproveitando dados do banco.
1645	20	2026-10-27 16:19:10.648951-04	info	[35/46] C2026827341 sem mudança de status ('Effective Contract'); reaproveitando dados do banco.
1646	20	2026-10-27 16:19:10.649127-04	info	[36/46] C2026827349 sem mudança de status ('Approval Completed'); reaproveitando dados do banco.
1647	20	2026-10-27 16:19:10.649317-04	info	[37/46] C2026827151 sem mudança de status ('Review Completed'); reaproveitando dados do banco.
1648	20	2026-10-27 16:19:10.649503-04	info	[38/46] C2026827137 sem mudança de status ('Review Completed'); reaproveitando dados do banco.
1649	20	2026-10-27 16:19:10.649674-04	info	[39/46] C2026827146 sem mudança de status ('Biz-Drop'); reaproveitando dados do banco.
1650	20	2026-10-27 16:19:10.649853-04	info	[40/46] C2026827161 sem mudança de status ('Request for Consent Rejected'); reaproveitando dados do banco.
1651	20	2026-10-27 16:19:10.650024-04	info	[41/46] C2026827166 sem mudança de status ('Legal Team Consent Completed'); reaproveitando dados do banco.
1652	20	2026-10-27 16:19:10.65019-04	info	[42/46] C2026826722 sem mudança de status ('Biz-Drop'); reaproveitando dados do banco.
1653	20	2026-10-27 16:19:10.650361-04	info	[43/46] C2026826100 sem mudança de status ('Approval Completed'); reaproveitando dados do banco.
1654	20	2026-10-27 16:19:10.650503-04	info	[44/46] Processando C2026825492
1655	20	2026-10-27 16:19:10.650556-04	info	Pesquisando contrato: C2026825492
1656	20	2026-10-27 16:19:24.359297-04	info	Tela de detalhe não foi recriada pelo SPA; recarregando a aba.
1657	20	2026-10-27 16:20:34.086378-04	info	C2026825492 coletado em 83.4s
1658	20	2026-10-27 16:20:34.104994-04	info	[45/46] C2026825327 sem mudança de status ('Effective Contract'); reaproveitando dados do banco.
1659	20	2026-10-27 16:20:34.105142-04	info	[46/46] C2026825339 sem mudança de status ('Biz-Drop'); reaproveitando dados do banco.
1660	20	2026-10-27 16:20:34.107524-04	info	46 contratos processados em 470.6s (3 extraídos do LMS, 42 reaproveitados do banco)
1661	20	2026-10-27 16:20:34.135431-04	info	Planilha consolidada salva em: /app/downloads/contract_review_management.xlsx (46 registros)
1664	20	2026-10-27 16:20:34.255003-04	success	Fluxo concluído com sucesso.
1665	21	2026-10-27 16:28:20.581048-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
1666	22	2026-10-27 16:38:07.11686-04	info	Execução solicitada pelo painel. Aguardando o robô assumir...
1667	22	2026-10-27 16:38:08.233572-04	info	Nenhum OTP prévio informado. Iniciando geração de OTP temporário...
1668	22	2026-10-27 16:38:08.233835-04	info	Iniciando obtenção de OTP para o usuário: legal.manaus
1669	22	2026-10-27 16:38:08.627445-04	info	1. Acessando página SSO: https://sso.lge.com/
1670	22	2026-10-27 16:38:13.813856-04	info	2. Clicando em Self-service OTP (#OTP)...
1671	22	2026-10-27 16:38:13.865777-04	info	3. Preenchendo senha e submetendo autenticação (#myButton)...
1672	22	2026-10-27 16:38:18.910096-04	info	4. Clicando em OTP temporário (.tempPw)...
1673	22	2026-10-27 16:38:20.132628-04	info	5. Tentativa 1/5 de validação do formulário...
1674	22	2026-10-27 16:38:21.807769-04	info	Captcha reconhecido: '6y2ek'
1675	22	2026-10-27 16:38:21.821714-04	info	Submetendo requisição e aguardando resposta da API...
1676	22	2026-10-27 16:38:22.75592-04	info	Resposta do serviço: 0#Temporary password has been sent to your PC outlook e-mail and mobile office on your smart phone. If you don't use either PC outlook e-mail or mobile office, please contact SPoC center(1544-3766/82-1544-3766).#488h0765
1677	22	2026-10-27 16:38:22.755997-04	info	OTP obtido com sucesso: 488h0765
1678	22	2026-10-27 16:38:22.779412-04	info	OTP temporário obtido para login: 488h0765
1679	22	2026-10-27 16:38:22.779608-04	info	Iniciando nova instância do navegador Playwright...
1680	22	2026-10-27 16:38:23.040678-04	info	Navegando para o portal de login: https://sso.lge.com/
1681	22	2026-10-27 16:38:23.884445-04	info	Preenchendo User ID e Senha corporativa...
1682	22	2026-10-27 16:38:27.951778-04	info	Aguardando campo #OTPPASSWORD e preenchendo token...
1683	22	2026-10-27 16:38:27.981926-04	info	Clicando no botão de login (#loginSsobtn)...
1684	22	2026-10-27 16:38:31.901042-04	info	Navegando para a página do LMS: https://lms.lge.com/#/app/dashboard
1685	22	2026-10-27 16:39:52.771882-04	info	Página posicionada com sucesso em: https://lms.lge.com/#/app/dashboard
1686	22	2026-10-27 16:39:52.802125-04	info	Navegando para a URL de busca de contratos: https://lms.lge.com/#/app/contract/search
1687	22	2026-10-27 16:39:55.804353-04	info	Filtrando por Subsidiary Code: LGESP...
1688	22	2026-10-27 16:39:55.976191-04	info	Filtrando por período de data (Request Date): 1...
1689	22	2026-10-27 16:39:59.854179-04	info	Iniciando o download do arquivo de exportação de contratos...
1690	22	2026-10-27 16:39:59.93801-04	info	Relatório de contratos salvo com sucesso em: /app/downloads/relatorio_contratos.xlsx
\.
SELECT pg_catalog.setval(pg_get_serial_sequence('public.execution_logs', 'id'), COALESCE((SELECT MAX(id) FROM public.execution_logs), 1), (SELECT MAX(id) IS NOT NULL FROM public.execution_logs));

-- Dados da tabela: rpa_jobs (19 registros)
COPY public.rpa_jobs (id, execution_id, requested_at, claimed_at, stop_requested) FROM stdin;
1	1	2026-10-15 16:59:59.121434-04	2026-10-15 17:00:01.170319-04	t
2	2	2026-10-15 17:02:09.896269-04	2026-10-15 17:02:10.359502-04	t
3	3	2026-10-15 17:03:50.847494-04	2026-10-15 17:03:52.517325-04	t
4	4	2026-10-16 14:10:54.039684-04	2026-10-16 14:10:55.17405-04	f
5	5	2026-10-16 14:16:54.285892-04	2026-10-16 14:16:55.504978-04	f
6	8	2026-10-16 14:32:43.734637-04	2026-10-16 14:32:46.257705-04	f
7	9	2026-10-16 14:38:08.973533-04	2026-10-16 14:38:09.94107-04	t
8	10	2026-10-16 14:41:50.221788-04	2026-10-16 14:41:50.358107-04	t
9	11	2026-10-16 15:04:57.846428-04	2026-10-16 15:04:58.05367-04	f
10	12	2026-10-16 15:42:58.557967-04	2026-10-16 15:42:58.860318-04	t
11	13	2026-10-16 15:57:50.140989-04	2026-10-16 15:57:50.382514-04	f
12	14	2026-10-16 15:58:19.588475-04	2026-10-16 15:58:19.988999-04	f
13	15	2026-10-16 15:58:25.685092-04	2026-10-16 15:58:26.698842-04	f
14	16	2026-10-16 15:59:01.316533-04	2026-10-16 15:59:02.122105-04	f
15	18	2026-10-27 14:58:57.974149-04	2026-10-27 14:58:58.522955-04	f
16	19	2026-10-27 16:08:45.165499-04	2026-10-27 16:08:45.63936-04	t
17	20	2026-10-27 16:10:45.644672-04	2026-10-27 16:10:45.975012-04	f
18	21	2026-10-27 16:28:20.581048-04	2026-10-27 16:28:21.553595-04	t
19	22	2026-10-27 16:38:07.11686-04	2026-10-27 16:38:07.476744-04	f
\.
SELECT pg_catalog.setval(pg_get_serial_sequence('public.rpa_jobs', 'id'), COALESCE((SELECT MAX(id) FROM public.rpa_jobs), 1), (SELECT MAX(id) IS NOT NULL FROM public.rpa_jobs));

-- Dados da tabela: contracts (45 registros)
COPY public.contracts (id, contract_number, management_number, counterparty, contract_name, contract_type, requester, department, progress_state, legal_reviewer, period_start, period_end, review_requested_at, legal_review_started_at, review_completed_at, consent_requested_at, consent_completed_at, approval_requested_at, approval_completed_at, effective_at, biz_drop_completed_at, currency, amount, flags, raw, last_execution_id, updated_at) FROM stdin;
1	C2026834490	C2026834490	S.S.M. CONSTRUCAO E COMERCIO DE EQUIPAMENTOS LTDA - ME	S S M CONSTRUCOES - Serviço para melhoria hidráulica na caixa d'água principal que abaste ce o complexo F1-F5.	General Services/Contracting	ANA SOUZA	LGESP GM/Environment Part - MAO	Legal Review in Progress	BARBARA LUSTOSA	2026-10-26	2026-12-31	2026-10-26	2026-10-26	\N	\N	\N	\N	\N	\N	\N	BRL	163962.22	{}	{"Contract number": "C2026834490", "Counterparty": "S.S.M. CONSTRUCAO E COMERCIO DE EQUIPAMENTOS LTDA - ME", "Contract name": "S S M CONSTRUCOES - Servi\\u00e7o para melhoria hidr\\u00e1ulica na caixa d'\\u00e1gua principal que abaste ce o complexo F1-F5.", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "ANA SOUZA", "Department of the person in charge": "LGESP GM/Environment Part - MAO", "Progress State": "Legal Review in Progress", "Start date": "2026-10-26", "End date": "2026-12-31", "Request Date": "2026-10-26", "Request Legal Review": "2026-10-26", "Review completed": null, "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "BARBARA LUSTOSA", "Contract currency": "BRL", "Amount": "163962.22"}	20	2026-10-27 16:20:34.236405-04
2	C2026834516	C2026834516	DXI - CENTRO DE INOVACAO E TRANSFORMACAO DIGITAL DA AMAZONIA LTDA	DXI - Contrato de Comodato de Bens de Informática de Prazo Determinado	Technology Joint Development	IAMILLY SOUZA	LGESP PPB & Business Intelligence Part - MAO	Legal Review in Progress	DYDRA ANDRADE	2026-11-30	2027-07-30	2026-10-26	2026-10-26	\N	\N	\N	\N	\N	\N	\N	BRL	42220.67	{}	{"Contract number": "C2026834516", "Counterparty": "DXI - CENTRO DE INOVACAO E TRANSFORMACAO DIGITAL DA AMAZONIA LTDA", "Contract name": "DXI - Contrato de Comodato de Bens de Inform\\u00e1tica de Prazo Determinado", "Main Contract Type": "Technology Exchange/Joint Development", "Contract type": "Technology Joint Development", "The person in charge": "IAMILLY SOUZA", "Department of the person in charge": "LGESP PPB & Business Intelligence Part - MAO", "Progress State": "Legal Review in Progress", "Start date": "2026-11-30", "End date": "2027-07-30", "Request Date": "2026-10-26", "Request Legal Review": "2026-10-26", "Review completed": null, "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "42220.67"}	20	2026-10-27 16:20:34.236405-04
3	C2026834065	C2026834065	HVAC ENGENHARIA, REPRESENTACAO E COMERCIO DE MAQUINAS E EQUIPAMENTOS LTDA - EPP	HVAC ENGENHARIA - Servico para Substituicao do Isolamento Termico das Tubulacoes de Agua Gelada - F3	General Services/Contracting	ANA SOUZA	LGESP GM/Environment Part - MAO	Review Completed	DYDRA ANDRADE	2026-10-21	2026-12-18	\N	2026-10-21	2026-10-23	\N	\N	\N	\N	\N	\N	BRL	200000	{}	{"Contract number": "C2026834065", "Counterparty": "HVAC ENGENHARIA, REPRESENTACAO E COMERCIO DE MAQUINAS E EQUIPAMENTOS LTDA - EPP", "Contract name": "HVAC ENGENHARIA - Servico para Substituicao do Isolamento Termico das Tubulacoes de Agua Gelada - F3", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "ANA SOUZA", "Department of the person in charge": "LGESP GM/Environment Part - MAO", "Progress State": "Review Completed", "Start date": "2026-10-21", "End date": "2026-12-18", "Request Date": null, "Request Legal Review": "2026-10-21", "Review completed": "2026-10-23", "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "200000.0"}	20	2026-10-27 16:20:34.236405-04
4	C2026833919	C2026833919	COMETAIS COMERCIO DE METAIS LTDA	Venda de resíduos metalicos com pagamento antecipado à remoção	Waste Management	JOSIANE ABREU	LGESP GM/Environment Part - MAO	Review Completed	DYDRA ANDRADE	2026-11-01	2027-03-01	2026-10-20	2026-10-20	2026-10-22	\N	\N	\N	\N	\N	\N	BRL	800000	{}	{"Contract number": "C2026833919", "Counterparty": "COMETAIS COMERCIO DE METAIS LTDA", "Contract name": "Venda de res\\u00edduos metalicos com pagamento antecipado \\u00e0 remo\\u00e7\\u00e3o", "Main Contract Type": "Service Utilization", "Contract type": "Waste Management", "The person in charge": "JOSIANE ABREU", "Department of the person in charge": "LGESP GM/Environment Part - MAO", "Progress State": "Review Completed", "Start date": "2026-11-01", "End date": "2027-03-01", "Request Date": "2026-10-20", "Request Legal Review": "2026-10-20", "Review completed": "2026-10-22", "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "800000.0"}	20	2026-10-27 16:20:34.236405-04
5	C2026833448	C2026833448	ALDO AZEVEDO OLIVEIRA	[ADDITIVE] Rental MAO for K-ISE Lee, Sumin	Leasing/Rental/Real Estate Transactions	MARCELLE CUNHA	LGESP GA Support Part - MAO	Legal Comments Provided	DYDRA ANDRADE	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	BRL	32368.68	{}	{"Contract number": "C2026833448", "Counterparty": "ALDO AZEVEDO OLIVEIRA", "Contract name": "[ADDITIVE] Rental MAO for K-ISE Lee, Sumin", "Main Contract Type": "Others", "Contract type": "Leasing/Rental/Real Estate Transactions", "The person in charge": "MARCELLE CUNHA", "Department of the person in charge": "LGESP GA Support Part - MAO", "Progress State": "Legal Comments Provided", "Start date": null, "End date": null, "Request Date": null, "Request Legal Review": null, "Review completed": null, "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "32368.68"}	20	2026-10-27 16:20:34.236405-04
6	C2026833165	C2026833165	SESI - SERVICO SOCIAL DA INDUSTRIA	SESI - SERVICOS PRESTADOS DE ERGONOMIA E FISIOTERAPIA DO TRABALHO	General Services/Contracting	IOMAR FALCAO	LGESP Safety Part - MAO	Review Completed	DYDRA ANDRADE	2026-11-01	2028-10-31	2026-10-13	2026-10-13	2026-10-23	\N	\N	\N	\N	\N	\N	BRL	810184.8	{}	{"Contract number": "C2026833165", "Counterparty": "SESI - SERVICO SOCIAL DA INDUSTRIA", "Contract name": "SESI - SERVICOS PRESTADOS DE ERGONOMIA E FISIOTERAPIA DO TRABALHO", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "IOMAR FALCAO", "Department of the person in charge": "LGESP Safety Part - MAO", "Progress State": "Review Completed", "Start date": "2026-11-01", "End date": "2028-10-31", "Request Date": "2026-10-13", "Request Legal Review": "2026-10-13", "Review completed": "2026-10-23", "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "810184.8"}	20	2026-10-27 16:20:34.236405-04
7	C2026833176	C2026833176	VISAO SERVICO DE INSTALACAO E MANUTENCAO DE MAQUINAS EIRELI	VISAO - SERVICOS DE ADEQUACAO DO SISTEMA DE COMBATE A INCENDIO E DETECCAO (FABRICAS LG)	General Services/Contracting	MARIA RODRIGUES	LGESP Safety Part - MAO	Legal Team Consent in Progress	DYDRA ANDRADE	2026-11-02	2027-04-02	2026-10-13	2026-10-13	2026-10-22	2026-10-23	\N	\N	\N	\N	\N	BRL	3800000	{}	{"Contract number": "C2026833176", "Counterparty": "VISAO SERVICO DE INSTALACAO E MANUTENCAO DE MAQUINAS EIRELI", "Contract name": "VISAO - SERVICOS DE ADEQUACAO DO SISTEMA DE COMBATE A INCENDIO E DETECCAO (FABRICAS LG)", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "MARIA RODRIGUES", "Department of the person in charge": "LGESP Safety Part - MAO", "Progress State": "Legal Team Consent in Progress", "Start date": "2026-11-02", "End date": "2027-04-02", "Request Date": "2026-10-13", "Request Legal Review": "2026-10-13", "Review completed": "2026-10-22", "Agreement request": "2026-10-23", "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "3800000.0"}	20	2026-10-27 16:20:34.236405-04
8	C2026832850	C2026832850	LG ELECTRONICS DA AMAZONIA LTDA	Teste - Legal Comments provided	General Services/Contracting	NICOLE QUEIROZ	LGESP Legal Mgmt. Part - MAO	Review Completed	DYDRA ANDRADE	2026-10-09	2026-10-31	\N	2026-10-09	2026-10-13	\N	\N	\N	\N	\N	\N	KRW	0	{}	{"Contract number": "C2026832850", "Counterparty": "LG ELECTRONICS DA AMAZONIA LTDA", "Contract name": "Teste - Legal Comments provided", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "NICOLE QUEIROZ", "Department of the person in charge": "LGESP Legal Mgmt. Part - MAO", "Progress State": "Review Completed", "Start date": "2026-10-09", "End date": "2026-10-31", "Request Date": null, "Request Legal Review": "2026-10-09", "Review completed": "2026-10-13", "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "KRW", "Amount": "0.0"}	20	2026-10-27 16:20:34.236405-04
9	C2026831822	C2026831822	M.C. BON	[Contract] Sales of Used Vehicle - MC Bon	Direct Sales	THAYNA MIRANDA	LGESP GA Support Part - MAO	Effective Contract	DYDRA ANDRADE	2026-09-29	2026-10-29	2026-09-29	2026-09-30	2026-10-05	2026-10-05	2026-10-05	2026-10-06	2026-10-06	2026-10-08	\N	BRL	257000	{"expired": false}	{"Contract number": "C2026831822", "Counterparty": "M.C. BON", "Contract name": "[Contract] Sales of Used Vehicle - MC Bon", "Main Contract Type": "Product sales", "Contract type": "Direct Sales", "The person in charge": "THAYNA MIRANDA", "Department of the person in charge": "LGESP GA Support Part - MAO", "Progress State": "Effective Contract", "Start date": "2026-09-29", "End date": "2026-10-29", "Request Date": "2026-09-29", "Request Legal Review": "2026-09-30", "Review completed": "2026-10-05", "Agreement request": "2026-10-05", "Agreement has been completed": "2026-10-05", "Approval request": "2026-10-06", "Approval request completed": "2026-10-06", "Register the conclusion of contract": "2026-10-08", "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "257000.0"}	20	2026-10-27 16:20:34.236405-04
10	C2026831823	C2026831823	EXP SOLAR COMERCIO, SERVICOS E IMPORTACAO LTDA - EPP	EXP SOLAR COMERCIO - Serviço para instalação de sistema de energia solar fotovotáico	General Services/Contracting	ANA SOUZA	LGESP GM/Environment Part - MAO	Legal Comments Provided	DYDRA ANDRADE	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	BRL	495000	{}	{"Contract number": "C2026831823", "Counterparty": "EXP SOLAR COMERCIO, SERVICOS E IMPORTACAO LTDA - EPP", "Contract name": "EXP SOLAR COMERCIO - Servi\\u00e7o para instala\\u00e7\\u00e3o de sistema de energia solar fotovot\\u00e1ico", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "ANA SOUZA", "Department of the person in charge": "LGESP GM/Environment Part - MAO", "Progress State": "Legal Comments Provided", "Start date": null, "End date": null, "Request Date": null, "Request Legal Review": null, "Review completed": null, "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "495000.0"}	20	2026-10-27 16:20:34.236405-04
41	C2026826722	C2026826722	BRUNA CAROLINE ALMEIDA MELO	[CONTRACT] New! Rental MAO for FSE Kim, Jae Hwan	Leasing/Rental/Real Estate Transactions	MARCELLE CUNHA	LGESP GA Support Part - MAO	Review Completed	BARBARA LUSTOSA	2026-08-01	2027-07-31	\N	2026-08-11	2026-08-14	\N	\N	\N	\N	\N	2026-09-01	BRL	66000	{}	{"Contract number": "C2026826722", "Counterparty": "BRUNA CAROLINE ALMEIDA MELO", "Contract name": "[CONTRACT] New! Rental MAO for FSE Kim, Jae Hwan", "Main Contract Type": "Others", "Contract type": "Leasing/Rental/Real Estate Transactions", "The person in charge": "MARCELLE CUNHA", "Department of the person in charge": "LGESP GA Support Part - MAO", "Progress State": "Review Completed", "Start date": "2026-08-01", "End date": "2027-07-31", "Request Date": null, "Request Legal Review": "2026-08-11", "Review completed": "2026-08-14", "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": "2026-09-01", "Reviewer": "BARBARA LUSTOSA", "Contract currency": "BRL", "Amount": "66000.0"}	20	2026-10-27 16:20:34.236405-04
11	C2026831469	C2026831469	CONSTRUTORA HOSS LTDA.	CONSTRUTORA HOSS LTDA - Serviço de consultoria e elaboração de projetos para construção de caixas de retardo de aguas pluviais de 5 fabricas	General Services/Contracting	ANA SOUZA	LGESP GM/Environment Part - MAO	Review Completed	DYDRA ANDRADE	2026-09-30	2026-12-18	2026-09-25	2026-09-25	2026-10-16	\N	\N	\N	\N	\N	\N	BRL	306040	{}	{"Contract number": "C2026831469", "Counterparty": "CONSTRUTORA HOSS LTDA.", "Contract name": "CONSTRUTORA HOSS LTDA - Servi\\u00e7o de consultoria e elabora\\u00e7\\u00e3o de projetos para constru\\u00e7\\u00e3o de caixas de retardo de aguas pluviais de 5 fabricas", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "ANA SOUZA", "Department of the person in charge": "LGESP GM/Environment Part - MAO", "Progress State": "Review Completed", "Start date": "2026-09-30", "End date": "2026-12-18", "Request Date": "2026-09-25", "Request Legal Review": "2026-09-25", "Review completed": "2026-10-16", "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "306040.0"}	20	2026-10-27 16:20:34.236405-04
12	C2026830501	C2026830501	INSTITUTO FEDERAL DE EDUCAÇÃO, CIÊNCIA E TECNOLOGIA DO AMAZONAS - IFAM	IFAM - 2° TERMO ADITIVO AO CONVÊNIO N° 005/2025	Technology Joint Development	IAMILLY SOUZA	LGESP PPB & Business Intelligence Part - MAO	Approval Completed	DYDRA ANDRADE	2026-11-15	2027-01-31	2026-09-16	2026-09-16	2026-09-22	2026-10-06	2026-10-06	2026-10-07	2026-10-16	\N	\N	BRL	2646879.49	{}	{"Contract number": "C2026830501", "Counterparty": "INSTITUTO FEDERAL DE EDUCA\\u00c7\\u00c3O, CI\\u00caNCIA E TECNOLOGIA DO AMAZONAS - IFAM", "Contract name": "IFAM - 2\\u00b0 TERMO ADITIVO AO CONV\\u00caNIO N\\u00b0 005/2025", "Main Contract Type": "Technology Exchange/Joint Development", "Contract type": "Technology Joint Development", "The person in charge": "IAMILLY SOUZA", "Department of the person in charge": "LGESP PPB & Business Intelligence Part - MAO", "Progress State": "Approval Completed", "Start date": "2026-11-15", "End date": "2027-01-31", "Request Date": "2026-09-16", "Request Legal Review": "2026-09-16", "Review completed": "2026-09-22", "Agreement request": "2026-10-06", "Agreement has been completed": "2026-10-06", "Approval request": "2026-10-07", "Approval request completed": "2026-10-16", "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "2646879.49"}	20	2026-10-27 16:20:34.236405-04
13	C2026830541	C2026830541	LX PANTOS SOLUCOES LOGISTICAS DO BRASIL LTDA	LX PANTOS Solutions - Contrato serviço de tercerização	Logistics	VERONICA MOTA	LGESP SCM Improvement Part - MAO	Approval Completed	DYDRA ANDRADE	2026-08-01	2028-07-31	\N	2026-09-21	2026-09-22	2026-10-02	2026-10-02	2026-10-02	2026-10-26	\N	\N	BRL	1	{}	{"Contract number": "C2026830541", "Counterparty": "LX PANTOS SOLUCOES LOGISTICAS DO BRASIL LTDA", "Contract name": "LX PANTOS Solutions - Contrato servi\\u00e7o de terceriza\\u00e7\\u00e3o", "Main Contract Type": "Service Utilization", "Contract type": "Logistics", "The person in charge": "VERONICA MOTA", "Department of the person in charge": "LGESP SCM Improvement Part - MAO", "Progress State": "Approval Completed", "Start date": "2026-08-01", "End date": "2028-07-31", "Request Date": null, "Request Legal Review": "2026-09-21", "Review completed": "2026-09-22", "Agreement request": "2026-10-02", "Agreement has been completed": "2026-10-02", "Approval request": "2026-10-02", "Approval request completed": "2026-10-26", "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "1.0"}	20	2026-10-27 16:20:34.236405-04
14	C2026830325	C2026830325	HAPVIDA ASSISTENCIA MEDICA LTDA.	HAPVIDA HEALTH PLAN CONTRACT RENEWAL_OS TEMPORARY MANPOWER_ Y26_Y28	Employment/Human Resources	LOIS SALAZAR	LGESP EA Part - MAO	Approval Completed	DYDRA ANDRADE	2026-09-01	2028-08-31	2026-09-15	2026-09-15	2026-10-02	2026-10-05	2026-10-05	2026-10-06	2026-10-08	\N	\N	BRL	1794671	{}	{"Contract number": "C2026830325", "Counterparty": "HAPVIDA ASSISTENCIA MEDICA LTDA.", "Contract name": "HAPVIDA HEALTH PLAN CONTRACT RENEWAL_OS TEMPORARY MANPOWER_ Y26_Y28", "Main Contract Type": "Others", "Contract type": "Employment/Human Resources", "The person in charge": "LOIS SALAZAR", "Department of the person in charge": "LGESP EA Part - MAO", "Progress State": "Approval Completed", "Start date": "2026-09-01", "End date": "2028-08-31", "Request Date": "2026-09-15", "Request Legal Review": "2026-09-15", "Review completed": "2026-10-02", "Agreement request": "2026-10-05", "Agreement has been completed": "2026-10-05", "Approval request": "2026-10-06", "Approval request completed": "2026-10-08", "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "1794671.0"}	20	2026-10-27 16:20:34.236405-04
15	C2026830332	C2026830332	HAPVIDA ASSISTENCIA MEDICA LTDA.	HAPVIDA DENTAL PLAN CONTRACT RENEWAL_OS TEMPORARY MANPOWER_ Y26_Y29	Employment/Human Resources	LOIS SALAZAR	LGESP EA Part - MAO	Effective Contract	DYDRA ANDRADE	2026-11-01	2029-10-31	2026-09-15	2026-09-15	2026-10-09	2026-10-13	2026-10-13	2026-10-14	2026-10-22	2026-10-23	\N	BRL	190026	{"expired": false}	{"Contract number": "C2026830332", "Counterparty": "HAPVIDA ASSISTENCIA MEDICA LTDA.", "Contract name": "HAPVIDA DENTAL PLAN CONTRACT RENEWAL_OS TEMPORARY MANPOWER_ Y26_Y29", "Main Contract Type": "Others", "Contract type": "Employment/Human Resources", "The person in charge": "LOIS SALAZAR", "Department of the person in charge": "LGESP EA Part - MAO", "Progress State": "Effective Contract", "Start date": "2026-11-01", "End date": "2029-10-31", "Request Date": "2026-09-15", "Request Legal Review": "2026-09-15", "Review completed": "2026-10-09", "Agreement request": "2026-10-13", "Agreement has been completed": "2026-10-13", "Approval request": "2026-10-14", "Approval request completed": "2026-10-22", "Register the conclusion of contract": "2026-10-23", "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "190026.0"}	20	2026-10-27 16:20:34.236405-04
16	C2026830319	C2026830319	HAPVIDA ASSISTENCIA MEDICA LTDA.	HAPVIDA HEALTH PLAN CONTRACT RENEWAL_REGULAR EMPLOYEES_ Y26_Y28	Employment/Human Resources	LOIS SALAZAR	LGESP EA Part - MAO	Effective Contract	DYDRA ANDRADE	2026-09-01	2028-08-31	2026-09-15	2026-09-15	2026-10-06	2026-10-06	2026-10-06	2026-10-06	2026-10-08	2026-10-23	\N	BRL	17728515	{"expired": false}	{"Contract number": "C2026830319", "Counterparty": "HAPVIDA ASSISTENCIA MEDICA LTDA.", "Contract name": "HAPVIDA HEALTH PLAN CONTRACT RENEWAL_REGULAR EMPLOYEES_ Y26_Y28", "Main Contract Type": "Others", "Contract type": "Employment/Human Resources", "The person in charge": "LOIS SALAZAR", "Department of the person in charge": "LGESP EA Part - MAO", "Progress State": "Effective Contract", "Start date": "2026-09-01", "End date": "2028-08-31", "Request Date": "2026-09-15", "Request Legal Review": "2026-09-15", "Review completed": "2026-10-06", "Agreement request": "2026-10-06", "Agreement has been completed": "2026-10-06", "Approval request": "2026-10-06", "Approval request completed": "2026-10-08", "Register the conclusion of contract": "2026-10-23", "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "17728515.0"}	20	2026-10-27 16:20:34.236405-04
17	C2026830310	C2026830310	GPBR PARTICIPACOES LTDA.	WELLHUB BENEFIT CONTRACT RENEWAL - Y26_Y29	General Services/Contracting	LOIS SALAZAR	LGESP EA Part - MAO	Effective Contract	BARBARA LUSTOSA	2026-10-01	2029-09-30	2026-09-15	2026-09-15	2026-10-05	2026-10-05	2026-10-06	2026-10-06	2026-10-09	2026-10-19	\N	BRL	144000	{"expired": false}	{"Contract number": "C2026830310", "Counterparty": "GPBR PARTICIPACOES LTDA.", "Contract name": "WELLHUB BENEFIT CONTRACT RENEWAL - Y26_Y29", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "LOIS SALAZAR", "Department of the person in charge": "LGESP EA Part - MAO", "Progress State": "Effective Contract", "Start date": "2026-10-01", "End date": "2029-09-30", "Request Date": "2026-09-15", "Request Legal Review": "2026-09-15", "Review completed": "2026-10-05", "Agreement request": "2026-10-05", "Agreement has been completed": "2026-10-06", "Approval request": "2026-10-06", "Approval request completed": "2026-10-09", "Register the conclusion of contract": "2026-10-19", "Biz-Drop Completed": null, "Reviewer": "BARBARA LUSTOSA", "Contract currency": "BRL", "Amount": "144000.0"}	20	2026-10-27 16:20:34.236405-04
18	C2026830337	C2026830337	ZENAIDE DA ROSA HENZEL	TERMINATION - Rental MAO for FSE Choi, Mun Geun	Leasing/Rental/Real Estate Transactions	MARCELLE CUNHA	LGESP GA Support Part - MAO	Approval Completed	DYDRA ANDRADE	2024-03-01	2026-09-04	\N	2026-09-15	2026-10-15	2026-10-19	2026-10-19	2026-10-19	2026-10-21	\N	\N	BRL	13275	{}	{"Contract number": "C2026830337", "Counterparty": "ZENAIDE DA ROSA HENZEL", "Contract name": "TERMINATION - Rental MAO for FSE Choi, Mun Geun", "Main Contract Type": "Others", "Contract type": "Leasing/Rental/Real Estate Transactions", "The person in charge": "MARCELLE CUNHA", "Department of the person in charge": "LGESP GA Support Part - MAO", "Progress State": "Approval Completed", "Start date": "2024-03-01", "End date": "2026-09-04", "Request Date": null, "Request Legal Review": "2026-09-15", "Review completed": "2026-10-15", "Agreement request": "2026-10-19", "Agreement has been completed": "2026-10-19", "Approval request": "2026-10-19", "Approval request completed": "2026-10-21", "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "13275.0"}	20	2026-10-27 16:20:34.236405-04
19	C2026830338	C2026830338	BRUNO CAMPOS PINTO DA SILVA	TERMINATION - Rental SP for FSE Choi, Mun Geun	Leasing/Rental/Real Estate Transactions	MARCELLE CUNHA	LGESP GA Support Part - MAO	Review Completed	DYDRA ANDRADE	2025-02-07	2026-09-06	2026-09-25	2026-09-28	2026-09-30	\N	\N	\N	\N	\N	\N	BRL	25612.05	{}	{"Contract number": "C2026830338", "Counterparty": "BRUNO CAMPOS PINTO DA SILVA", "Contract name": "TERMINATION - Rental SP for FSE Choi, Mun Geun", "Main Contract Type": "Others", "Contract type": "Leasing/Rental/Real Estate Transactions", "The person in charge": "MARCELLE CUNHA", "Department of the person in charge": "LGESP GA Support Part - MAO", "Progress State": "Review Completed", "Start date": "2025-02-07", "End date": "2026-09-06", "Request Date": "2026-09-25", "Request Legal Review": "2026-09-28", "Review completed": "2026-09-30", "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "25612.05"}	20	2026-10-27 16:20:34.236405-04
20	C2026830326	C2026830326	HAPVIDA ASSISTENCIA MEDICA LTDA.	HAPVIDA DENTAL PLAN CONTRACT RENEWAL_REGULAR EMPLOYEES_ Y26_Y29	Employment/Human Resources	LOIS SALAZAR	LGESP EA Part - MAO	Effective Contract	DYDRA ANDRADE	2026-11-01	2029-10-31	2026-09-15	2026-09-15	2026-10-09	2026-10-13	2026-10-13	2026-10-14	2026-10-22	2026-10-23	\N	BRL	1111086	{"expired": false}	{"Contract number": "C2026830326", "Counterparty": "HAPVIDA ASSISTENCIA MEDICA LTDA.", "Contract name": "HAPVIDA DENTAL PLAN CONTRACT RENEWAL_REGULAR EMPLOYEES_ Y26_Y29", "Main Contract Type": "Others", "Contract type": "Employment/Human Resources", "The person in charge": "LOIS SALAZAR", "Department of the person in charge": "LGESP EA Part - MAO", "Progress State": "Effective Contract", "Start date": "2026-11-01", "End date": "2029-10-31", "Request Date": "2026-09-15", "Request Legal Review": "2026-09-15", "Review completed": "2026-10-09", "Agreement request": "2026-10-13", "Agreement has been completed": "2026-10-13", "Approval request": "2026-10-14", "Approval request completed": "2026-10-22", "Register the conclusion of contract": "2026-10-23", "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "1111086.0"}	20	2026-10-27 16:20:34.236405-04
21	C2026830018	C2026830018	JAKS INDUSTRIA E COMERCIO DE PAPEL LTDA	[CONTRACT] Paper Towel & Toilet Dispensers - Loan and Supply - Jaks Industria	General Services/Contracting	CAMILLE SILVA	LGESP GA Support Part - MAO	Approval Completed	DYDRA ANDRADE	2026-07-30	2028-07-30	\N	2026-09-14	2026-10-07	2026-10-15	2026-10-16	2026-10-23	2026-10-26	\N	\N	BRL	42996.36	{}	{"Contract number": "C2026830018", "Counterparty": "JAKS INDUSTRIA E COMERCIO DE PAPEL LTDA", "Contract name": "[CONTRACT] Paper Towel & Toilet Dispensers - Loan and Supply - Jaks Industria", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "CAMILLE SILVA", "Department of the person in charge": "LGESP GA Support Part - MAO", "Progress State": "Approval Completed", "Start date": "2026-07-30", "End date": "2028-07-30", "Request Date": null, "Request Legal Review": "2026-09-14", "Review completed": "2026-10-07", "Agreement request": "2026-10-15", "Agreement has been completed": "2026-10-16", "Approval request": "2026-10-23", "Approval request completed": "2026-10-26", "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "42996.36"}	20	2026-10-27 16:20:34.236405-04
22	C2026830050	C2026830050	LG CNS Co., Ltd.	LG CNS Korea - GMES 2.0 Application Project - 2nd Phase	General Services/Contracting	KELLY OLIVEIRA	LGESP IT CNS Team - MAO	Effective Contract	BARBARA LUSTOSA	2026-06-05	2026-11-30	2026-09-11	2026-09-14	2026-09-29	2026-09-30	2026-09-30	2026-09-30	2026-10-02	2026-10-20	\N	USD	1169835	{"expired": false}	{"Contract number": "C2026830050", "Counterparty": "LG CNS Co., Ltd.", "Contract name": "LG CNS Korea - GMES 2.0 Application Project - 2nd Phase", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "KELLY OLIVEIRA", "Department of the person in charge": "LGESP IT CNS Team - MAO", "Progress State": "Effective Contract", "Start date": "2026-06-05", "End date": "2026-11-30", "Request Date": "2026-09-11", "Request Legal Review": "2026-09-14", "Review completed": "2026-09-29", "Agreement request": "2026-09-30", "Agreement has been completed": "2026-09-30", "Approval request": "2026-09-30", "Approval request completed": "2026-10-02", "Register the conclusion of contract": "2026-10-20", "Biz-Drop Completed": null, "Reviewer": "BARBARA LUSTOSA", "Contract currency": "USD", "Amount": "1169835.0"}	20	2026-10-27 16:20:34.236405-04
23	C2026829737	C2026829737	MARIA GERALDA DE SOUZA	TERMINATION - Rental MAO for FSE Kim, Seonwoo	Leasing/Rental/Real Estate Transactions	MARCELLE CUNHA	LGESP GA Support Part - MAO	Legal Team Consent Completed	DYDRA ANDRADE	2024-03-01	2026-09-01	2026-09-09	2026-09-14	2026-10-15	2026-10-19	2026-10-19	\N	\N	\N	\N	BRL	1200	{}	{"Contract number": "C2026829737", "Counterparty": "MARIA GERALDA DE SOUZA", "Contract name": "TERMINATION - Rental MAO for FSE Kim, Seonwoo", "Main Contract Type": "Others", "Contract type": "Leasing/Rental/Real Estate Transactions", "The person in charge": "MARCELLE CUNHA", "Department of the person in charge": "LGESP GA Support Part - MAO", "Progress State": "Legal Team Consent Completed", "Start date": "2024-03-01", "End date": "2026-09-01", "Request Date": "2026-09-09", "Request Legal Review": "2026-09-14", "Review completed": "2026-10-15", "Agreement request": "2026-10-19", "Agreement has been completed": "2026-10-19", "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "1200.0"}	20	2026-10-27 16:20:34.236405-04
24	C2026829743	C2026829743	TELEFONICA BRASIL S.A	[CONTRACT NEW] LEASE OF LG MANAUS SITE FOR ANTENNA AND TELEPHONY INST. VIVO - 2026/2028	Leasing/Rental/Real Estate Transactions	EDYANDRA SILVA	LGESP GA Support Part - MAO	Review Completed	DYDRA ANDRADE	2026-10-01	2028-09-30	2026-09-09	2026-09-14	2026-09-14	\N	\N	\N	\N	\N	\N	BRL	105600	{}	{"Contract number": "C2026829743", "Counterparty": "TELEFONICA BRASIL S.A", "Contract name": "[CONTRACT NEW] LEASE OF LG MANAUS SITE FOR ANTENNA AND TELEPHONY INST. VIVO - 2026/2028", "Main Contract Type": "Others", "Contract type": "Leasing/Rental/Real Estate Transactions", "The person in charge": "EDYANDRA SILVA", "Department of the person in charge": "LGESP GA Support Part - MAO", "Progress State": "Review Completed", "Start date": "2026-10-01", "End date": "2028-09-30", "Request Date": "2026-09-09", "Request Legal Review": "2026-09-14", "Review completed": "2026-09-14", "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "105600.0"}	20	2026-10-27 16:20:34.236405-04
25	C2026829481	C2026829481	LG CNS BRASIL SERVICOS DE T.I. LTDA	LG CNS Brasil - LOCAL DX and CCTV	General Services/Contracting	KELLY OLIVEIRA	LGESP IT CNS Team - MAO	Effective Contract	BARBARA LUSTOSA	2026-06-01	2027-05-31	2026-09-07	2026-09-08	2026-10-13	2026-10-14	2026-10-16	2026-10-16	2026-10-20	2026-10-22	\N	BRL	686491	{"expired": false}	{"Contract number": "C2026829481", "Counterparty": "LG CNS BRASIL SERVICOS DE T.I. LTDA", "Contract name": "LG CNS Brasil - LOCAL DX and CCTV", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "KELLY OLIVEIRA", "Department of the person in charge": "LGESP IT CNS Team - MAO", "Progress State": "Effective Contract", "Start date": "2026-06-01", "End date": "2027-05-31", "Request Date": "2026-09-07", "Request Legal Review": "2026-09-08", "Review completed": "2026-10-13", "Agreement request": "2026-10-14", "Agreement has been completed": "2026-10-16", "Approval request": "2026-10-16", "Approval request completed": "2026-10-20", "Register the conclusion of contract": "2026-10-22", "Biz-Drop Completed": null, "Reviewer": "BARBARA LUSTOSA", "Contract currency": "BRL", "Amount": "686491.0"}	20	2026-10-27 16:20:34.236405-04
26	C2026829335	C2026829335	MATHEUS MARTINS	[FINANCIAL AGREEMENT] Sinister - LGE / ALD TEE4A36	Finance/Insurance	MARCELLE CUNHA	LGESP GA Support Part - MAO	Legal Team Consent Completed	DYDRA ANDRADE	2026-08-15	2028-09-15	2026-09-04	2026-09-08	2026-10-05	2026-10-07	2026-10-08	\N	\N	\N	\N	BRL	3000	{}	{"Contract number": "C2026829335", "Counterparty": "MATHEUS MARTINS", "Contract name": "[FINANCIAL AGREEMENT] Sinister - LGE / ALD TEE4A36", "Main Contract Type": "Others", "Contract type": "Finance/Insurance", "The person in charge": "MARCELLE CUNHA", "Department of the person in charge": "LGESP GA Support Part - MAO", "Progress State": "Legal Team Consent Completed", "Start date": "2026-08-15", "End date": "2028-09-15", "Request Date": "2026-09-04", "Request Legal Review": "2026-09-08", "Review completed": "2026-10-05", "Agreement request": "2026-10-07", "Agreement has been completed": "2026-10-08", "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "3000.0"}	20	2026-10-27 16:20:34.236405-04
27	C2026829228	C2026829228	TECNORADIO COMERCIO E SOLUCOES EM COMUNICACAO LTDA	Tecnoradio Contract	Logistics	VERONICA MOTA	LGESP SCM Improvement Part - MAO	Effective Contract	DYDRA ANDRADE	2026-06-26	2028-06-25	\N	2026-09-08	2026-10-05	2026-10-05	2026-10-06	2026-10-09	2026-10-19	2026-10-21	\N	BRL	38544	{"expired": false}	{"Contract number": "C2026829228", "Counterparty": "TECNORADIO COMERCIO E SOLUCOES EM COMUNICACAO LTDA", "Contract name": "Tecnoradio Contract", "Main Contract Type": "Service Utilization", "Contract type": "Logistics", "The person in charge": "VERONICA MOTA", "Department of the person in charge": "LGESP SCM Improvement Part - MAO", "Progress State": "Effective Contract", "Start date": "2026-06-26", "End date": "2028-06-25", "Request Date": null, "Request Legal Review": "2026-09-08", "Review completed": "2026-10-05", "Agreement request": "2026-10-05", "Agreement has been completed": "2026-10-06", "Approval request": "2026-10-09", "Approval request completed": "2026-10-19", "Register the conclusion of contract": "2026-10-21", "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "38544.0"}	20	2026-10-27 16:20:34.236405-04
28	C2026828532	C2026828532	BRADESCO SAUDE S/A	[CONTRACT] CONTRACT_ANNUAL PRICE ADJUSTMENT- HEALTH PLAN BRADESCO - Y26_Y28	Employment/Human Resources	LOIS SALAZAR	LGESP EA Part - MAO	Effective Contract	DYDRA ANDRADE	2026-08-01	2028-07-31	2026-08-27	2026-08-27	2026-08-31	2026-09-01	2026-09-01	2026-09-01	2026-09-02	2026-09-04	\N	BRL	8168888	{"expired": false}	{"Contract number": "C2026828532", "Counterparty": "BRADESCO SAUDE S/A", "Contract name": "[CONTRACT] CONTRACT_ANNUAL PRICE ADJUSTMENT- HEALTH PLAN BRADESCO - Y26_Y28", "Main Contract Type": "Others", "Contract type": "Employment/Human Resources", "The person in charge": "LOIS SALAZAR", "Department of the person in charge": "LGESP EA Part - MAO", "Progress State": "Effective Contract", "Start date": "2026-08-01", "End date": "2028-07-31", "Request Date": "2026-08-27", "Request Legal Review": "2026-08-27", "Review completed": "2026-08-31", "Agreement request": "2026-09-01", "Agreement has been completed": "2026-09-01", "Approval request": "2026-09-01", "Approval request completed": "2026-09-02", "Register the conclusion of contract": "2026-09-04", "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "8168888.0"}	20	2026-10-27 16:20:34.236405-04
29	C2026828391	C2026828391	HVAC ENGENHARIA, REPRESENTACAO E COMERCIO DE MAQUINAS E EQUIPAMENTOS LTDA - EPP	HVAC ENGENHARIA - CONTRATO DE MANUTENCAO DOS CHILLERS DAS FABRICAS 1, 3 E 5	General Services/Contracting	ANA SOUZA	LGESP GM/Environment Part - MAO	Approval Completed	DYDRA ANDRADE	2026-09-01	2028-08-30	\N	2026-08-26	2026-10-08	2026-10-09	2026-10-13	2026-10-19	2026-10-24	\N	\N	BRL	108000	{}	{"Contract number": "C2026828391", "Counterparty": "HVAC ENGENHARIA, REPRESENTACAO E COMERCIO DE MAQUINAS E EQUIPAMENTOS LTDA - EPP", "Contract name": "HVAC ENGENHARIA - CONTRATO DE MANUTENCAO DOS CHILLERS DAS FABRICAS 1, 3 E 5", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "ANA SOUZA", "Department of the person in charge": "LGESP GM/Environment Part - MAO", "Progress State": "Approval Completed", "Start date": "2026-09-01", "End date": "2028-08-30", "Request Date": null, "Request Legal Review": "2026-08-26", "Review completed": "2026-10-08", "Agreement request": "2026-10-09", "Agreement has been completed": "2026-10-13", "Approval request": "2026-10-19", "Approval request completed": "2026-10-24", "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "108000.0"}	20	2026-10-27 16:20:34.236405-04
30	C2025811697	C2025811697	BRASANITAS EMPRESA BRASILEIRA DE SANEAMENTO E COM LTDA	BRASANITAS - Aditivo - Readjustment Service of Logistics	General Services/Contracting	TATIANE GALDENCIO	LGESP MS Material 1 Section - MAO	Effective Contract	BARBARA LUSTOSA	2025-06-01	2028-05-31	2025-03-25	2025-03-25	2026-04-14	2025-06-06	2025-06-09	2025-06-13	2026-04-18	2026-05-05	\N	BRL	15228000	{"expired": false}	{"Contract number": "C2025811697", "Counterparty": "BRASANITAS EMPRESA BRASILEIRA DE SANEAMENTO E COM LTDA", "Contract name": "BRASANITAS - Aditivo - Readjustment Service of Logistics", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "TATIANE GALDENCIO", "Department of the person in charge": "LGESP MS Material 1 Section - MAO", "Progress State": "Effective Contract", "Start date": "2025-06-01", "End date": "2028-05-31", "Request Date": "2025-03-25", "Request Legal Review": "2025-03-25", "Review completed": "2026-04-14", "Agreement request": "2025-06-06", "Agreement has been completed": "2025-06-09", "Approval request": "2025-06-13", "Approval request completed": "2026-04-18", "Register the conclusion of contract": "2026-05-05", "Biz-Drop Completed": null, "Reviewer": "BARBARA LUSTOSA", "Contract currency": "BRL", "Amount": "15228000.0"}	20	2026-10-27 16:20:34.236405-04
31	C2026827793	C2026827793	Fortreck	NDA - Consultoria para serviços	General Services/Contracting	SIMEIA BATALHA	LGESP General Procurement Part - MAO	Review Completed	BARBARA LUSTOSA	2026-09-01	2026-10-31	2026-08-20	2026-08-20	2026-08-25	\N	\N	\N	\N	\N	2026-08-26	BRL	50000	{}	{"Contract number": "C2026827793", "Counterparty": "Fortreck", "Contract name": "NDA - Consultoria para servi\\u00e7os", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "SIMEIA BATALHA", "Department of the person in charge": "LGESP General Procurement Part - MAO", "Progress State": "Review Completed", "Start date": "2026-09-01", "End date": "2026-10-31", "Request Date": "2026-08-20", "Request Legal Review": "2026-08-20", "Review completed": "2026-08-25", "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": "2026-08-26", "Reviewer": "BARBARA LUSTOSA", "Contract currency": "BRL", "Amount": "50000.0"}	20	2026-10-27 16:20:34.236405-04
32	C2026827791	C2026827791	Deloitte	NDA - Consultoria para serviços (Deloitte)	General Services/Contracting	SIMEIA BATALHA	LGESP General Procurement Part - MAO	Review Completed	BARBARA LUSTOSA	2026-09-01	2026-10-31	2026-08-20	2026-08-20	2026-08-25	\N	\N	\N	\N	\N	2026-08-26	BRL	50000	{}	{"Contract number": "C2026827791", "Counterparty": "Deloitte", "Contract name": "NDA - Consultoria para servi\\u00e7os (Deloitte)", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "SIMEIA BATALHA", "Department of the person in charge": "LGESP General Procurement Part - MAO", "Progress State": "Review Completed", "Start date": "2026-09-01", "End date": "2026-10-31", "Request Date": "2026-08-20", "Request Legal Review": "2026-08-20", "Review completed": "2026-08-25", "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": "2026-08-26", "Reviewer": "BARBARA LUSTOSA", "Contract currency": "BRL", "Amount": "50000.0"}	20	2026-10-27 16:20:34.236405-04
33	C2026827335	C2026827335	IBBI-INSTITUTO BRASILEIRO DE BIOTECNOLOGIA E INOVACAO	2° TERMO ADITIVO AO CONVÊNIO DE COOPERAÇÃO CIENTÍFICA E TECNOLÓGICA N° 001 / 2025 CELEBRADO ENTRE LG ELECTRONICS DO BRASIL LTDA E IBBI - Projeto AI Smartprod	Technology Joint Development	IAMILLY SOUZA	LGESP PPB & Business Intelligence Part - MAO	Contract Expired	BARBARA LUSTOSA	2025-10-01	2026-09-30	\N	2026-08-17	2026-09-16	2026-09-15	2026-09-16	2026-09-16	2026-09-24	\N	\N	BRL	2458455.44	{"expired": true}	{"Contract number": "C2026827335", "Counterparty": "IBBI-INSTITUTO BRASILEIRO DE BIOTECNOLOGIA E INOVACAO", "Contract name": "2\\u00b0 TERMO ADITIVO AO CONV\\u00caNIO DE COOPERA\\u00c7\\u00c3O CIENT\\u00cdFICA E TECNOL\\u00d3GICA N\\u00b0 001 / 2025 CELEBRADO ENTRE LG ELECTRONICS DO BRASIL LTDA E IBBI - Projeto AI Smartprod", "Main Contract Type": "Technology Exchange/Joint Development", "Contract type": "Technology Joint Development", "The person in charge": "IAMILLY SOUZA", "Department of the person in charge": "LGESP PPB & Business Intelligence Part - MAO", "Progress State": "Contract Expired", "Start date": "2025-10-01", "End date": "2026-09-30", "Request Date": null, "Request Legal Review": "2026-08-17", "Review completed": "2026-09-16", "Agreement request": "2026-09-15", "Agreement has been completed": "2026-09-16", "Approval request": "2026-09-16", "Approval request completed": "2026-09-24", "Register the conclusion of contract": "Expirado", "Biz-Drop Completed": null, "Reviewer": "BARBARA LUSTOSA", "Contract currency": "BRL", "Amount": "2458455.44"}	20	2026-10-27 16:20:34.236405-04
34	C2026827341	C2026827341	LRS TECNOLOGIA LTDA	LRS TECNOLOGIA - CONTRATO DE LOCAÇÃO DE EQUIPAMENTOS	Technology Joint Development	IAMILLY SOUZA	LGESP PPB & Business Intelligence Part - MAO	Effective Contract	BARBARA LUSTOSA	2026-07-31	2028-07-30	2026-08-17	2026-08-17	2026-10-02	2026-10-02	2026-10-02	2026-10-05	2026-10-08	2026-10-19	\N	BRL	153849.83	{"expired": false}	{"Contract number": "C2026827341", "Counterparty": "LRS TECNOLOGIA LTDA", "Contract name": "LRS TECNOLOGIA - CONTRATO DE LOCA\\u00c7\\u00c3O DE EQUIPAMENTOS", "Main Contract Type": "Technology Exchange/Joint Development", "Contract type": "Technology Joint Development", "The person in charge": "IAMILLY SOUZA", "Department of the person in charge": "LGESP PPB & Business Intelligence Part - MAO", "Progress State": "Effective Contract", "Start date": "2026-07-31", "End date": "2028-07-30", "Request Date": "2026-08-17", "Request Legal Review": "2026-08-17", "Review completed": "2026-10-02", "Agreement request": "2026-10-02", "Agreement has been completed": "2026-10-02", "Approval request": "2026-10-05", "Approval request completed": "2026-10-08", "Register the conclusion of contract": "2026-10-19", "Biz-Drop Completed": null, "Reviewer": "BARBARA LUSTOSA", "Contract currency": "BRL", "Amount": "153849.83"}	20	2026-10-27 16:20:34.236405-04
35	C2026827349	C2026827349	FUNDACAO AMAZONICA DE AMPARO A PESQUISA E DESENVOLVIMENTO TECNOLOGICO DESEMBARGADOR PAULO DOS ANJOS FEITO	FPF - CONTRATO DE COMODATO DE BENS DE INFORMÁTICA POR PRAZO DETERMINADO.	Leasing/Rental/Real Estate Transactions	IAMILLY SOUZA	LGESP PPB & Business Intelligence Part - MAO	Approval Completed	DYDRA ANDRADE	\N	\N	2026-08-17	2026-08-17	2026-09-24	2026-09-15	2026-09-16	2026-09-16	2026-10-07	\N	\N	BRL	70512	{}	{"Contract number": "C2026827349", "Counterparty": "FUNDACAO AMAZONICA DE AMPARO A PESQUISA E DESENVOLVIMENTO TECNOLOGICO DESEMBARGADOR PAULO DOS ANJOS FEITO", "Contract name": "FPF - CONTRATO DE COMODATO DE BENS DE INFORM\\u00c1TICA POR PRAZO DETERMINADO.", "Main Contract Type": "Others", "Contract type": "Leasing/Rental/Real Estate Transactions", "The person in charge": "IAMILLY SOUZA", "Department of the person in charge": "LGESP PPB & Business Intelligence Part - MAO", "Progress State": "Approval Completed", "Start date": "DATA INV\\u00c1LIDA", "End date": "DATA INV\\u00c1LIDA", "Request Date": "2026-08-17", "Request Legal Review": "2026-08-17", "Review completed": "2026-09-24", "Agreement request": "2026-09-15", "Agreement has been completed": "2026-09-16", "Approval request": "2026-09-16", "Approval request completed": "2026-10-07", "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "70512.0"}	20	2026-10-27 16:20:34.236405-04
36	C2026827151	C2026827151	CARLOS ALBERTO ALVES JUNIOR	Termination Rental SP for FSE Son, Jichul	Leasing/Rental/Real Estate Transactions	MARCELLE CUNHA	LGESP GA Support Part - MAO	Review Completed	DYDRA ANDRADE	2026-07-09	2026-07-24	2026-08-14	2026-08-17	2026-10-22	2026-08-28	2026-08-31	\N	\N	\N	\N	BRL	22200	{}	{"Contract number": "C2026827151", "Counterparty": "CARLOS ALBERTO ALVES JUNIOR", "Contract name": "Termination Rental SP for FSE Son, Jichul", "Main Contract Type": "Others", "Contract type": "Leasing/Rental/Real Estate Transactions", "The person in charge": "MARCELLE CUNHA", "Department of the person in charge": "LGESP GA Support Part - MAO", "Progress State": "Review Completed", "Start date": "2026-07-09", "End date": "2026-07-24", "Request Date": "2026-08-14", "Request Legal Review": "2026-08-17", "Review completed": "2026-10-22", "Agreement request": "2026-08-28", "Agreement has been completed": "2026-08-31", "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "22200.0"}	20	2026-10-27 16:20:34.236405-04
37	C2026827137	C2026827137	RGC CONSULT. E ENGENHARIA S/C LTDA	[RENEWAL CONTRACT] Consultancy Service Fiscal Classification of Goods - NCM	General Services/Contracting	ADRIANA AMORIM	LGESP HS Code Mgmt. Part - MAO	Review Completed	DYDRA ANDRADE	2026-09-01	2028-08-31	\N	2026-08-13	2026-09-14	\N	\N	\N	\N	\N	\N	BRL	55374.96	{}	{"Contract number": "C2026827137", "Counterparty": "RGC CONSULT. E ENGENHARIA S/C LTDA", "Contract name": "[RENEWAL CONTRACT] Consultancy Service Fiscal Classification of Goods - NCM", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "ADRIANA AMORIM", "Department of the person in charge": "LGESP HS Code Mgmt. Part - MAO", "Progress State": "Review Completed", "Start date": "2026-09-01", "End date": "2028-08-31", "Request Date": null, "Request Legal Review": "2026-08-13", "Review completed": "2026-09-14", "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "55374.96"}	20	2026-10-27 16:20:34.236405-04
38	C2026827146	C2026827146	FABIO GOMES NAVECA	[CONTRACT] New! Rental MAO for FSE Kim, Seonwoo	Leasing/Rental/Real Estate Transactions	MARCELLE CUNHA	LGESP GA Support Part - MAO	Review Completed	BARBARA LUSTOSA	2026-09-01	2027-08-31	\N	2026-08-13	2026-08-18	\N	\N	\N	\N	\N	2026-08-26	BRL	72000	{}	{"Contract number": "C2026827146", "Counterparty": "FABIO GOMES NAVECA", "Contract name": "[CONTRACT] New! Rental MAO for FSE Kim, Seonwoo", "Main Contract Type": "Others", "Contract type": "Leasing/Rental/Real Estate Transactions", "The person in charge": "MARCELLE CUNHA", "Department of the person in charge": "LGESP GA Support Part - MAO", "Progress State": "Review Completed", "Start date": "2026-09-01", "End date": "2027-08-31", "Request Date": null, "Request Legal Review": "2026-08-13", "Review completed": "2026-08-18", "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": "2026-08-26", "Reviewer": "BARBARA LUSTOSA", "Contract currency": "BRL", "Amount": "72000.0"}	20	2026-10-27 16:20:34.236405-04
39	C2026827161	C2026827161	CONCESSIONARIA DOS AEROPORTOS DA AMAZONIA S/A	VINCI CONCESSIONARIA DOS AEROPORTOS Contract	Logistics	VERONICA MOTA	LGESP SCM Improvement Part - MAO	Request for Consent Rejected	DYDRA ANDRADE	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	BRL	0	{}	{"Contract number": "C2026827161", "Counterparty": "CONCESSIONARIA DOS AEROPORTOS DA AMAZONIA S/A", "Contract name": "VINCI CONCESSIONARIA DOS AEROPORTOS Contract", "Main Contract Type": "Service Utilization", "Contract type": "Logistics", "The person in charge": "VERONICA MOTA", "Department of the person in charge": "LGESP SCM Improvement Part - MAO", "Progress State": "Request for Consent Rejected", "Start date": null, "End date": null, "Request Date": null, "Request Legal Review": null, "Review completed": null, "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "0.0"}	20	2026-10-27 16:20:34.236405-04
40	C2026827166	C2026827166	ELIZABETH DOS SANTOS OLIVEIRA	Termination Rental MAO for K-ISE Kim, Min Ho	Leasing/Rental/Real Estate Transactions	MARCELLE CUNHA	LGESP GA Support Part - MAO	Legal Team Consent Completed	DYDRA ANDRADE	2024-01-08	2026-07-31	2026-08-31	2026-08-31	2026-10-15	2026-10-19	2026-10-20	\N	\N	\N	\N	BRL	3430.9	{}	{"Contract number": "C2026827166", "Counterparty": "ELIZABETH DOS SANTOS OLIVEIRA", "Contract name": "Termination Rental MAO for K-ISE Kim, Min Ho", "Main Contract Type": "Others", "Contract type": "Leasing/Rental/Real Estate Transactions", "The person in charge": "MARCELLE CUNHA", "Department of the person in charge": "LGESP GA Support Part - MAO", "Progress State": "Legal Team Consent Completed", "Start date": "2024-01-08", "End date": "2026-07-31", "Request Date": "2026-08-31", "Request Legal Review": "2026-08-31", "Review completed": "2026-10-15", "Agreement request": "2026-10-19", "Agreement has been completed": "2026-10-20", "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "3430.9"}	20	2026-10-27 16:20:34.236405-04
42	C2026826100	C2026826100	ISABELA DE CARVALHO PINTO VIANA	Termination Rental MAO for FSE Kim, Jae Hwan	Leasing/Rental/Real Estate Transactions	MARCELLE CUNHA	LGESP GA Support Part - MAO	Approval Completed	DYDRA ANDRADE	2026-02-01	2026-07-31	\N	2026-08-04	2026-10-15	2026-10-15	2026-10-16	2026-10-19	2026-10-21	\N	\N	BRL	6000	{}	{"Contract number": "C2026826100", "Counterparty": "ISABELA DE CARVALHO PINTO VIANA", "Contract name": "Termination Rental MAO for FSE Kim, Jae Hwan", "Main Contract Type": "Others", "Contract type": "Leasing/Rental/Real Estate Transactions", "The person in charge": "MARCELLE CUNHA", "Department of the person in charge": "LGESP GA Support Part - MAO", "Progress State": "Approval Completed", "Start date": "2026-02-01", "End date": "2026-07-31", "Request Date": null, "Request Legal Review": "2026-08-04", "Review completed": "2026-10-15", "Agreement request": "2026-10-15", "Agreement has been completed": "2026-10-16", "Approval request": "2026-10-19", "Approval request completed": "2026-10-21", "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "BRL", "Amount": "6000.0"}	20	2026-10-27 16:20:34.236405-04
43	C2026825492	C2026825492	WON AUTOMATION KOREA CO., LTD	WonAutomation Korea CO., LTD. - DPS 2.0 LICENSE	Technology Joint Development	ANDERCLEY FILHO	LGESP MS Maintenance Section - MAO	Legal Comments Provided	DYDRA ANDRADE	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	USD	34400	{}	{"Contract number": "C2026825492", "Counterparty": "WON AUTOMATION KOREA CO., LTD", "Contract name": "WonAutomation Korea CO., LTD. - DPS 2.0 LICENSE", "Main Contract Type": "Technology Exchange/Joint Development", "Contract type": "Technology Joint Development", "The person in charge": "ANDERCLEY FILHO", "Department of the person in charge": "LGESP MS Maintenance Section - MAO", "Progress State": "Legal Comments Provided", "Start date": null, "End date": null, "Request Date": null, "Request Legal Review": null, "Review completed": null, "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": null, "Reviewer": "DYDRA ANDRADE", "Contract currency": "USD", "Amount": "34400.0"}	20	2026-10-27 16:20:34.236405-04
44	C2026825327	C2026825327	ACTAR CONNECTIVITY ENGENHARIA DE TELECOMUNICACOES LTDA	Support Contract Renew for GMES 1.0 L4 Switches	General Services/Contracting	KELLY OLIVEIRA	LGESP IT CNS Team - MAO	Effective Contract	BARBARA LUSTOSA	2026-12-01	2027-11-30	2026-07-28	2026-07-28	2026-08-06	2026-08-06	2026-08-06	2026-08-12	2026-08-13	2026-08-19	\N	USD	11145.04	{"expired": false}	{"Contract number": "C2026825327", "Counterparty": "ACTAR CONNECTIVITY ENGENHARIA DE TELECOMUNICACOES LTDA", "Contract name": "Support Contract Renew for GMES 1.0 L4 Switches", "Main Contract Type": "Service Utilization", "Contract type": "General Services/Contracting", "The person in charge": "KELLY OLIVEIRA", "Department of the person in charge": "LGESP IT CNS Team - MAO", "Progress State": "Effective Contract", "Start date": "2026-12-01", "End date": "2027-11-30", "Request Date": "2026-07-28", "Request Legal Review": "2026-07-28", "Review completed": "2026-08-06", "Agreement request": "2026-08-06", "Agreement has been completed": "2026-08-06", "Approval request": "2026-08-12", "Approval request completed": "2026-08-13", "Register the conclusion of contract": "2026-08-19", "Biz-Drop Completed": null, "Reviewer": "BARBARA LUSTOSA", "Contract currency": "USD", "Amount": "11145.04"}	20	2026-10-27 16:20:34.236405-04
45	C2026825339	C2026825339	AG Automoveis	[CONTRACT] Sales of Used Vehicle	Direct Sales	THAYNA MIRANDA	LGESP GA Support Part - MAO	Review Completed	BARBARA LUSTOSA	\N	\N	2026-07-28	2026-07-29	2026-09-09	\N	\N	\N	\N	\N	2026-09-29	BRL	330000000	{}	{"Contract number": "C2026825339", "Counterparty": "AG Automoveis", "Contract name": "[CONTRACT] Sales of Used Vehicle", "Main Contract Type": "Product sales", "Contract type": "Direct Sales", "The person in charge": "THAYNA MIRANDA", "Department of the person in charge": "LGESP GA Support Part - MAO", "Progress State": "Review Completed", "Start date": "DATA INV\\u00c1LIDA", "End date": "DATA INV\\u00c1LIDA", "Request Date": "2026-07-28", "Request Legal Review": "2026-07-29", "Review completed": "2026-09-09", "Agreement request": null, "Agreement has been completed": null, "Approval request": null, "Approval request completed": null, "Register the conclusion of contract": null, "Biz-Drop Completed": "2026-09-29", "Reviewer": "BARBARA LUSTOSA", "Contract currency": "BRL", "Amount": "330000000.0"}	20	2026-10-27 16:20:34.236405-04
\.
SELECT pg_catalog.setval(pg_get_serial_sequence('public.contracts', 'id'), COALESCE((SELECT MAX(id) FROM public.contracts), 1), (SELECT MAX(id) IS NOT NULL FROM public.contracts));

