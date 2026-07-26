# Provider Contract

## Purpose

This document defines the adapter interface every document analysis provider must implement. Providers are integrations, not the core domain. They receive storage keys and return storage keys -- they never touch domain entities directly.

## ProviderAdapter Interface

Every provider must implement the `ProviderAdapter` abstract base class.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ProviderCapabilities:
    has_ocr: bool
    has_table_extraction: bool
    has_reading_order: bool
    has_formula: bool
    has_image_description: bool

@dataclass
class ProviderInput:
    source_storage_key: str
    source_mime_type: str
    config: dict

@dataclass
class RawArtifact:
    artifact_type: str  # "raw_json" | "raw_markdown" | "raw_html"
    storage_key: str
    format: str         # "json" | "md" | "html"

@dataclass
class ProviderOutput:
    raw_artifacts: list[RawArtifact]
    metadata: dict      # provider-specific runtime metadata

@dataclass
class ProviderError(Exception):
    error_code: str
    error_message: str
    recoverable: bool

class ProviderAdapter(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str: ...

    @property
    @abstractmethod
    def provider_version(self) -> str: ...

    @property
    @abstractmethod
    def supported_mime_types(self) -> list[str]: ...

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities: ...

    @abstractmethod
    def execute(self, input: ProviderInput) -> ProviderOutput: ...
```

## Input Contract

`ProviderInput` contains:

| Field | Type | Description |
|-------|------|-------------|
| `source_storage_key` | `str` | Storage key to resolve the source file via `StorageService.resolve()` |
| `source_mime_type` | `str` | MIME type of the source file (e.g. `application/pdf`) |
| `config` | `dict` | Provider-specific configuration passed through from the user's request |

The adapter resolves the file path by calling `StorageService.resolve(source_storage_key)`.

## Output Contract

`ProviderOutput` contains:

| Field | Type | Description |
|-------|------|-------------|
| `raw_artifacts` | `list[RawArtifact]` | One or more raw output files stored via `StorageService` |
| `metadata` | `dict` | Runtime metadata (processing time, pages processed, warnings) |

Each `RawArtifact` records:

| Field | Type | Description |
|-------|------|-------------|
| `artifact_type` | `str` | `"raw_json"`, `"raw_markdown"`, or `"raw_html"` |
| `storage_key` | `str` | Storage key for the saved raw output |
| `format` | `str` | File format: `"json"`, `"md"`, `"html"` |

## Error Contract

`ProviderError` is raised when the provider fails:

| Field | Type | Description |
|-------|------|-------------|
| `error_code` | `str` | Machine-readable code (e.g. `"TIMEOUT"`, `"CORRUPT_INPUT"`) |
| `error_message` | `str` | Human-readable description |
| `recoverable` | `bool` | Whether retrying might succeed |

## Normalizer Contract

Each provider must also provide a normalizer function that converts its raw output into the application-owned `RenderDocument`:

```python
def normalize(raw_json: dict, provider_metadata: dict) -> RenderDocument: ...
```

The normalizer:
- Receives the raw JSON output loaded from the `RawArtifact.storage_key`
- Receives `provider_metadata` with `provider_id`, `provider_version`, `raw_artifact_storage_key`, `normalized_at`
- Returns a `RenderDocument` (see `RENDER_DOCUMENT_SCHEMA.md`)
- Must normalize all coordinates to `[0, 1]` top-left origin
- Must use canonical `block_type` names so the frontend overlay renders correctly (see `ANNOTATION_OVERLAY_PIPELINE.md`)

## Provider Definition (Registry)

Each provider registers a `ProviderDefinition`:

```python
@dataclass
class ProviderDefinition:
    provider_id: str
    display_name: str
    version: str
    capabilities: ProviderCapabilities
    supported_mime_types: list[str]
    config_schema: dict       # JSON Schema for provider config
    queue_name: str           # Celery queue name
    timeout_seconds: int
```

## Rules

1. Provider adapters must NOT import or depend on domain entities.
2. Provider adapters must NOT access the database.
3. Provider adapters must NOT modify files in place -- they create new artifacts.
4. Provider adapters must save raw output via `StorageService` and return storage keys.
5. Each provider has its own Celery queue (e.g. `analysis.docling`, `analysis.opendataloader`).
6. Provider containers are isolated -- separate Docker images with their own dependencies.

## Registered Providers

### Docling

| Property | Value |
|----------|-------|
| `provider_id` | `"docling"` |
| `queue_name` | `"analysis.docling"` |
| `supported_mime_types` | `["application/pdf"]` |
| Python package | `docling>=2.14.0` |
| Raw output format | JSON (Docling DoclingDocument) |
| OCR | No (local mode) |
| Timeout | 300s |

### OpenDataLoader

| Property | Value |
|----------|-------|
| `provider_id` | `"opendataloader"` |
| `queue_name` | `"analysis.opendataloader"` |
| `supported_mime_types` | `["application/pdf"]` |
| Python package | `opendataloader-pdf` |
| Raw output format | JSON |
| System requirement | Java 11+ |
| OCR | Yes (hybrid mode) |
| Timeout | 600s |
