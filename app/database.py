"""
AIVENTRA — Supabase PostgreSQL Async Database Client
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg

from app.config import settings
from app.core.exceptions import CaseNotFoundError, DatabaseError

# Module-level connection pool (initialised on startup)
_pool: asyncpg.Pool | None = None

# ------------------------------------------------------------------
# Pool lifecycle
# ------------------------------------------------------------------

async def init_db() -> None:
    """Create the asyncpg connection pool and ensure schema exists."""
    global _pool
    dsn = str(settings.DATABASE_URL).replace("postgresql+asyncpg://", "postgresql://")
    _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)
    await _create_schema()


async def close_db() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise DatabaseError("Database pool is not initialised.")
    return _pool


# ------------------------------------------------------------------
# Schema bootstrap
# ------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS cases (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename    TEXT NOT NULL,
    file_type   TEXT NOT NULL,
    file_path   TEXT,
    status      TEXT NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS injuries (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id       UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    wound_type    TEXT,
    body_location TEXT,
    bbox          JSONB,
    confidence    FLOAT,
    severity      TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS image_findings (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id      UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    image_path   TEXT,
    caption      TEXT,
    description  TEXT,
    model_used   TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS toxicology (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id       UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    substance     TEXT,
    concentration FLOAT,
    unit          TEXT,
    notes         TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS forensic_entities (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id      UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    entity_type  TEXT,
    entity_value TEXT,
    source       TEXT,
    confidence   FLOAT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS embeddings (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id    UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding  FLOAT8[],
    model_used TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reports (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id          UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    summary          TEXT,
    reasoning_model  TEXT,
    raw_output       TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


async def _create_schema() -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(_SCHEMA_SQL)


# ------------------------------------------------------------------
# Cases CRUD
# ------------------------------------------------------------------

async def create_case(filename: str, file_type: str, file_path: str = "") -> Dict[str, Any]:
    pool = get_pool()
    async with pool.acquire() as conn:
        # Ensure column exists (idempotent migration)
        await conn.execute(
            "ALTER TABLE cases ADD COLUMN IF NOT EXISTS file_path TEXT"
        )
        row = await conn.fetchrow(
            """
            INSERT INTO cases (filename, file_type, file_path, status)
            VALUES ($1, $2, $3, 'pending')
            RETURNING id, filename, file_type, file_path, status, created_at
            """,
            filename,
            file_type,
            file_path,
        )
    return dict(row)


async def get_case(case_id: str) -> Dict[str, Any]:
    import asyncpg
    pool = get_pool()
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM cases WHERE id = $1", case_id)
        if not row:
            raise CaseNotFoundError(f"Case {case_id} not found.")
        return dict(row)
    except asyncpg.exceptions.DataError as e:
        if "invalid UUID" in str(e):
            raise CaseNotFoundError(f"Case {case_id} not found (invalid format).")
        raise


async def update_case_status(case_id: str, status: str) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE cases SET status=$1, updated_at=NOW() WHERE id=$2",
            status,
            case_id,
        )


async def get_full_case(case_id: str) -> Dict[str, Any]:
    """Return case + all related records."""
    case = await get_case(case_id)
    pool = get_pool()
    async with pool.acquire() as conn:
        injuries = [dict(r) for r in await conn.fetch(
            "SELECT * FROM injuries WHERE case_id=$1", case_id)]
        image_findings = [dict(r) for r in await conn.fetch(
            "SELECT * FROM image_findings WHERE case_id=$1", case_id)]
        tox = [dict(r) for r in await conn.fetch(
            "SELECT * FROM toxicology WHERE case_id=$1", case_id)]
        entities = [dict(r) for r in await conn.fetch(
            "SELECT * FROM forensic_entities WHERE case_id=$1", case_id)]
        reports = [dict(r) for r in await conn.fetch(
            "SELECT * FROM reports WHERE case_id=$1", case_id)]

    case["injuries"] = injuries
    case["image_findings"] = image_findings
    case["toxicology"] = tox
    case["forensic_entities"] = entities
    case["reports"] = reports
    return case


# ------------------------------------------------------------------
# Injuries
# ------------------------------------------------------------------

async def insert_injuries(case_id: str, injuries: List[Dict[str, Any]]) -> None:
    if not injuries:
        return
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO injuries (case_id, wound_type, body_location, bbox, confidence, severity)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            [
                (
                    case_id,
                    inj.get("wound_type"),
                    inj.get("body_location"),
                    json.dumps(inj.get("bbox")) if inj.get("bbox") else None,
                    inj.get("confidence"),
                    inj.get("severity"),
                )
                for inj in injuries
            ],
        )


# ------------------------------------------------------------------
# Image Findings
# ------------------------------------------------------------------

async def insert_image_finding(
    case_id: str,
    image_path: str,
    caption: str,
    description: str,
    model_used: str,
) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO image_findings (case_id, image_path, caption, description, model_used)
            VALUES ($1, $2, $3, $4, $5)
            """,
            case_id, image_path, caption, description, model_used,
        )


# ------------------------------------------------------------------
# Toxicology
# ------------------------------------------------------------------

async def insert_toxicology(case_id: str, records: List[Dict[str, Any]]) -> None:
    if not records:
        return
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO toxicology (case_id, substance, concentration, unit, notes)
            VALUES ($1, $2, $3, $4, $5)
            """,
            [(case_id, r.get("substance"), r.get("concentration"), r.get("unit"), r.get("notes"))
             for r in records],
        )


# ------------------------------------------------------------------
# Forensic Entities
# ------------------------------------------------------------------

async def insert_forensic_entities(case_id: str, entities: List[Dict[str, Any]]) -> None:
    if not entities:
        return
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO forensic_entities (case_id, entity_type, entity_value, source, confidence)
            VALUES ($1, $2, $3, $4, $5)
            """,
            [(case_id, e.get("entity_type"), e.get("entity_value"), e.get("source"), e.get("confidence"))
             for e in entities],
        )


# ------------------------------------------------------------------
# Embeddings
# ------------------------------------------------------------------

async def insert_embeddings(case_id: str, chunks: List[Dict[str, Any]]) -> None:
    """Store chunk texts and their embedding vectors."""
    if not chunks:
        return
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO embeddings (case_id, chunk_text, embedding, model_used)
            VALUES ($1, $2, $3, $4)
            """,
            [(case_id, c["text"], c["embedding"], c.get("model_used", "bge-large"))
             for c in chunks],
        )


# ------------------------------------------------------------------
# Reports
# ------------------------------------------------------------------

async def insert_report(
    case_id: str,
    summary: str,
    reasoning_model: str,
    raw_output: str,
) -> Dict[str, Any]:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO reports (case_id, summary, reasoning_model, raw_output)
            VALUES ($1, $2, $3, $4)
            RETURNING id, case_id, summary, reasoning_model, created_at
            """,
            case_id, summary, reasoning_model, raw_output,
        )
    return dict(row)
