# API Specification

## Base Path

All API endpoints are under `/api`.

## Source Documents

### POST /api/documents

Upload a source document.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | `file` | Yes | The document file (PDF) |

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "name": "report.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 1048576,
  "storage_key": "ab/cdef...",
  "checksum": "md5hash",
  "page_count": 10,
  "page_dimensions": [
    {"page_index": 0, "width": 612.0, "height": 792.0}
  ],
  "created_at": "2024-12-31T12:00:00Z",
  "updated_at": "2024-12-31T12:00:00Z"
}
```

### GET /api/documents

List source documents.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `offset` | `int` | 0 | Pagination offset |
| `limit` | `int` | 50 | Page size (max 100) |

**Response:** `200 OK`

```json
{
  "items": [SourceDocumentDTO],
  "total": 42,
  "offset": 0,
  "limit": 50
}
```

### GET /api/documents/{document_id}

Get source document metadata.

**Response:** `200 OK` -- Single `SourceDocumentDTO`

### GET /api/documents/{document_id}/download

Download the source file.

**Response:** `200 OK` -- Binary file with `Content-Disposition: attachment`

## Analysis Runs

### POST /api/documents/{document_id}/analysis-runs

Create an analysis run for a document.

**Request:**

```json
{
  "provider_id": "docling",
  "config": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider_id` | `str` | Yes | Provider to use |
| `config` | `dict` | No | Provider-specific configuration |

The run is created in `PENDING` state, then immediately dispatched (transitions to `QUEUED`).

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "source_document_id": "uuid",
  "provider_id": "docling",
  "provider_version": "2.14.0",
  "status": "queued",
  "requested_config": {},
  "created_at": "2024-12-31T12:00:00Z"
}
```

### GET /api/documents/{document_id}/analysis-runs

List analysis runs for a document.

**Response:** `200 OK`

```json
{
  "items": [AnalysisRunDTO]
}
```

### GET /api/analysis-runs/{run_id}

Get analysis run status.

**Response:** `200 OK` -- Single `AnalysisRunDTO`

```json
{
  "id": "uuid",
  "source_document_id": "uuid",
  "provider_id": "docling",
  "provider_version": "2.14.0",
  "status": "success",
  "requested_config": {},
  "runtime_metadata": {"processing_time_seconds": 12.5},
  "started_at": "2024-12-31T12:00:01Z",
  "finished_at": "2024-12-31T12:00:13Z",
  "error_code": null,
  "error_message": null,
  "artifacts": [
    {
      "id": "uuid",
      "artifact_type": "raw_json",
      "format": "json"
    },
    {
      "id": "uuid",
      "artifact_type": "render_document",
      "format": "json"
    }
  ],
  "created_at": "2024-12-31T12:00:00Z",
  "updated_at": "2024-12-31T12:00:13Z"
}
```

### GET /api/analysis-runs/{run_id}/render

Get the RenderDocument for a completed run.

**Response:** `200 OK` -- Full `RenderDocument` JSON (see `RENDER_DOCUMENT_SCHEMA.md`)

**Error:** `409 Conflict` if run status is not `SUCCESS`.

### GET /api/analysis-runs/{run_id}/artifacts/{artifact_id}

Download a raw artifact file.

**Response:** `200 OK` -- Binary file

## Providers

### GET /api/providers

List available providers and their capabilities.

**Response:** `200 OK`

```json
[
  {
    "provider_id": "docling",
    "display_name": "Docling",
    "version": "2.x",
    "capabilities": {
      "has_ocr": false,
      "has_table_extraction": true,
      "has_reading_order": true,
      "has_formula": false,
      "has_image_description": false
    },
    "supported_mime_types": ["application/pdf"]
  },
  {
    "provider_id": "opendataloader",
    "display_name": "OpenDataLoader PDF",
    "version": "2.x",
    "capabilities": {
      "has_ocr": true,
      "has_table_extraction": true,
      "has_reading_order": true,
      "has_formula": true,
      "has_image_description": true
    },
    "supported_mime_types": ["application/pdf"]
  }
]
```

## Error Responses

All errors follow a consistent format:

```json
{
  "status_code": 400,
  "detail": "Human-readable message",
  "error_code": "VALIDATION_ERROR"
}
```

Standard error codes:

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | State conflict (e.g. run not ready) |
| `PROVIDER_NOT_FOUND` | 400 | Unknown provider_id |
| `RUN_NOT_SUCCESS` | 409 | Run has not completed successfully |
