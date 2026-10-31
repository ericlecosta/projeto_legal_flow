#!/usr/bin/env python3
"""
Exporta os dados atuais do banco PostgreSQL (lms_legal) para db_init/01_seed.sql.

Como a porta 5432 do container lms_postgres está exposta localmente, este script
conecta direto via socket TCP (protocolo nativo do PostgreSQL, sem depender de
sudo docker ou pg_dump instalado na máquina host) e gera o dump completo em
db_init/01_seed.sql pronto para ser carregado automaticamente pelo Postgres em
outra máquina via /docker-entrypoint-initdb.d.

Uso:
    python3 scripts/export_db.py
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import socket
import struct
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_SQL = ROOT_DIR / "db_init" / "01_seed.sql"


def load_env() -> dict[str, str]:
    env = dict(os.environ)
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip("'").strip('"'))
    return env


def pg_connect(host: str, port: int, user: str, password: str, database: str):
    s = socket.create_connection((host, port), timeout=10)
    payload = f"\x00\x03\x00\x00user\x00{user}\x00database\x00{database}\x00\x00".encode()
    s.sendall(struct.pack("!I", len(payload) + 4) + payload)

    def recv_msg() -> tuple[str, bytes]:
        hdr = b""
        while len(hdr) < 5:
            chunk = s.recv(5 - len(hdr))
            if not chunk:
                raise EOFError("Conexão encerrada pelo PostgreSQL.")
            hdr += chunk
        mtype = chr(hdr[0])
        mlen = struct.unpack("!I", hdr[1:5])[0] - 4
        body = b""
        while len(body) < mlen:
            chunk = s.recv(mlen - len(body))
            if not chunk:
                raise EOFError("Conexão encerrada durante leitura.")
            body += chunk
        return mtype, body

    mtype, body = recv_msg()
    if mtype == "R":
        auth_code = struct.unpack("!I", body[:4])[0]
        if auth_code == 10:  # SASL SCRAM-SHA-256
            nonce = base64.b64encode(os.urandom(18)).decode()
            c_first_bare = f"n=,r={nonce}"
            c_first = f"n,,{c_first_bare}".encode()
            mech = b"SCRAM-SHA-256\x00" + struct.pack("!I", len(c_first)) + c_first
            s.sendall(b"p" + struct.pack("!I", len(mech) + 4) + mech)

            mtype, body = recv_msg()
            if mtype != "R" or struct.unpack("!I", body[:4])[0] != 11:
                raise RuntimeError(f"Resposta SASL inesperada: {mtype}")
            s_first = body[4:].decode()
            parts = dict(item.split("=", 1) for item in s_first.split(","))
            r_nonce = parts["r"]
            salt = base64.b64decode(parts["s"])
            iters = int(parts["i"])

            salted_pw = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iters)
            client_key = hmac.new(salted_pw, b"Client Key", hashlib.sha256).digest()
            stored_key = hashlib.sha256(client_key).digest()
            c_final_without_proof = f"c=biws,r={r_nonce}"
            auth_msg = f"{c_first_bare},{s_first},{c_final_without_proof}".encode()
            client_sig = hmac.new(stored_key, auth_msg, hashlib.sha256).digest()
            proof = base64.b64encode(bytes(a ^ b for a, b in zip(client_key, client_sig))).decode()
            c_final = f"{c_final_without_proof},p={proof}".encode()
            s.sendall(b"p" + struct.pack("!I", len(c_final) + 4) + c_final)

    while True:
        mtype, body = recv_msg()
        if mtype == "Z":
            break
        if mtype == "E":
            raise RuntimeError(f"Erro de autenticação no PostgreSQL: {body!r}")

    return s, recv_msg


def pg_copy_out(s: socket.socket, recv_msg, table: str, columns: list[str]) -> tuple[list[str], int]:
    cols_sql = ", ".join(columns)
    sql = f"COPY public.{table} ({cols_sql}) TO STDOUT;\x00".encode()
    s.sendall(b"Q" + struct.pack("!I", len(sql) + 4) + sql)
    lines: list[str] = []
    while True:
        mtype, body = recv_msg()
        if mtype == "d":  # CopyData
            lines.append(body.decode("utf-8"))
        elif mtype == "c":  # CopyDone
            pass
        elif mtype == "Z":  # ReadyForQuery
            break
        elif mtype == "E":
            raise RuntimeError(f"Erro ao exportar {table}: {body!r}")
    return lines, len(lines)


DDL_HEADER = """-- =============================================================================
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
"""

TABLES: list[tuple[str, list[str]]] = [
    (
        "executions",
        [
            "id",
            "flow",
            "status",
            "trigger",
            "started_at",
            "finished_at",
            "duration_seconds",
            "records",
            "error_title",
            "error_message",
            "error_screenshot_url",
        ],
    ),
    (
        "execution_steps",
        ["id", "execution_id", "position", "key", "label", "status", "duration_seconds"],
    ),
    (
        "execution_logs",
        ["id", "execution_id", "timestamp", "level", "message"],
    ),
    (
        "rpa_jobs",
        ["id", "execution_id", "requested_at", "claimed_at", "stop_requested"],
    ),
    (
        "contracts",
        [
            "id",
            "contract_number",
            "management_number",
            "counterparty",
            "contract_name",
            "contract_type",
            "requester",
            "department",
            "progress_state",
            "legal_reviewer",
            "period_start",
            "period_end",
            "review_requested_at",
            "legal_review_started_at",
            "review_completed_at",
            "consent_requested_at",
            "consent_completed_at",
            "approval_requested_at",
            "approval_completed_at",
            "effective_at",
            "biz_drop_completed_at",
            "currency",
            "amount",
            "flags",
            "raw",
            "last_execution_id",
            "updated_at",
        ],
    ),
]


def main() -> None:
    env = load_env()
    host = env.get("POSTGRES_HOST", "localhost")
    port = int(env.get("POSTGRES_PORT", "5432"))
    user = env.get("POSTGRES_USER", "postgres")
    password = env.get("POSTGRES_PASSWORD", "postgres")
    database = env.get("POSTGRES_DB", "lms_legal")

    OUTPUT_SQL.parent.mkdir(parents=True, exist_ok=True)
    s, recv_msg = pg_connect(host, port, user, password, database)

    try:
        chunks = [DDL_HEADER.strip(), ""]
        counts: dict[str, int] = {}
        for table, cols in TABLES:
            lines, count = pg_copy_out(s, recv_msg, table, cols)
            counts[table] = count
            cols_sql = ", ".join(cols)
            chunks.append(f"-- Dados da tabela: {table} ({count} registros)")
            chunks.append(f"COPY public.{table} ({cols_sql}) FROM stdin;")
            if lines:
                chunks.append("".join(lines).rstrip("\n"))
            chunks.append("\\.")
            chunks.append(
                f"SELECT pg_catalog.setval(pg_get_serial_sequence('public.{table}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM public.{table}), 1), "
                f"(SELECT MAX(id) IS NOT NULL FROM public.{table}));"
            )
            chunks.append("")

        OUTPUT_SQL.write_text("\n".join(chunks) + "\n", encoding="utf-8")
        print(f"Dump exportado com sucesso para: {OUTPUT_SQL}")
        for table, count in counts.items():
            print(f"  - {table}: {count} registros")
    finally:
        s.close()


if __name__ == "__main__":
    main()
