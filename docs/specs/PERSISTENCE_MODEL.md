# Persistence Model

## Storage Classes

### Metadata Storage

PostgreSQL for all entity metadata, relationships, and status tracking.

### Artifact Storage

Filesystem-based `StorageService` (content-addressable, MD5 hash keys) for source files, raw provider output, and render documents. In production, this would be S3/MinIO.

## PostgreSQL Tables

### source_document

The original uploaded file.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` | |
| `name` | `VARCHAR(255)` | NOT NULL | Original filename |
| `mime_type` | `VARCHAR(100)` | NOT NULL | MIME type |
| `size_bytes` | `BIGINT` | NOT NULL | File size |
| `storage_key` | `VARCHAR(64)` | UNIQUE, NOT NULL | Content hash key in artifact storage |
| `checksum` | `VARCHAR(32)` | NOT NULL | MD5 checksum |
| `page_count` | `INTEGER` | NOT NULL, default 0 | Number of pages |
| `page_dimensions` | `JSONB` | NOT NULL, default `'[]'` | Per-page dimensions: `[{"page_index": 0, "width": 612.0, "height": 792.0}]` |
| `uploaded_by` | `VARCHAR(255)` | NULLABLE | Future: user identity |
| `slug` | `VARCHAR(255)` | UNIQUE | URL-friendly identifier |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | |

Indexes:
- `ix_source_document_storage_key` on `storage_key` (unique)
- `ix_source_document_slug` on `slug` (unique)
- `ix_source_document_created_at` on `created_at`

### analysis_run

One provider's analysis of one source document.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` | |
| `source_document_id` | `UUID` | FK -> `source_document.id`, NOT NULL | |
| `provider_id` | `VARCHAR(50)` | NOT NULL | Provider identifier |
| `provider_version` | `VARCHAR(20)` | NOT NULL, default `''` | Provider software version |
| `status` | `VARCHAR(20)` | NOT NULL, default `'pending'` | `pending`, `queued`, `running`, `success`, `failed`, `cancelled` |
| `requested_config` | `JSONB` | NOT NULL, default `'{}'` | Provider config snapshot |
| `runtime_metadata` | `JSONB` | NULLABLE | Processing metadata (time, warnings) |
| `started_at` | `TIMESTAMPTZ` | NULLABLE | |
| `finished_at` | `TIMESTAMPTZ` | NULLABLE | |
| `error_code` | `VARCHAR(50)` | NULLABLE | Machine-readable error code |
| `error_message` | `TEXT` | NULLABLE | Human-readable error |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | |

CHECK constraint on `status`: `status IN ('pending', 'queued', 'running', 'success', 'failed', 'cancelled')`

Indexes:
- `ix_analysis_run_source_document_id` on `source_document_id`
- `ix_analysis_run_status` on `status`
- `ix_analysis_run_provider_id` on `provider_id`

### analysis_artifact

Stored output from an analysis run.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` | |
| `analysis_run_id` | `UUID` | FK -> `analysis_run.id`, NOT NULL | |
| `artifact_type` | `VARCHAR(30)` | NOT NULL | `raw_json`, `raw_markdown`, `raw_html`, `render_document` |
| `format` | `VARCHAR(10)` | NOT NULL | `json`, `md`, `html` |
| `storage_key` | `VARCHAR(64)` | NOT NULL | Content hash key |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | |

CHECK constraint on `artifact_type`: `artifact_type IN ('raw_json', 'raw_markdown', 'raw_html', 'render_document')`

Indexes:
- `ix_analysis_artifact_run_id` on `analysis_run_id`
- `ix_analysis_artifact_type` on `artifact_type`

### comparison_session

A user-facing comparison grouping.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` | |
| `source_document_id` | `UUID` | FK -> `source_document.id`, NOT NULL | |
| `created_by` | `VARCHAR(255)` | NULLABLE | Future: user identity |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | |

### comparison_session_runs (join table)

Many-to-many between comparison sessions and analysis runs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `comparison_session_id` | `UUID` | FK -> `comparison_session.id`, NOT NULL | |
| `analysis_run_id` | `UUID` | FK -> `analysis_run.id`, NOT NULL | |

PK: `(comparison_session_id, analysis_run_id)`

## Entity-Relationship Diagram

```
source_document 1───* analysis_run
analysis_run    1───* analysis_artifact
source_document 1───* comparison_session
comparison_session *───* analysis_run  (via comparison_session_runs)
```

## Migration Strategy

1. Create new tables (`source_document`, `analysis_run`, `analysis_artifact`, `comparison_session`, `comparison_session_runs`).
2. Keep old `file` and `analysed_doc` tables temporarily during transition.
3. Drop old tables in a follow-up migration after Phase 5 cleanup.
