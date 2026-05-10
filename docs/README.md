# Docs Index

This directory contains the design and handoff documents for the target architecture of the project.

These documents are intended to let another coding agent continue implementation work without re-deriving the architectural decisions.

## Read Order

1. `ARCHITECTURE_HANDOFF.md`
2. `architecture/ARCHITECTURE.md`
3. `architecture/DOMAIN_MODEL.md`
4. `architecture/TESTING_STRATEGY.md`
5. `specs/RENDER_DOCUMENT_SCHEMA.md`
6. `specs/PROVIDER_CONTRACT.md`
7. `specs/API_SPEC.md`
8. `specs/PERSISTENCE_MODEL.md`
9. `product/BACKGROUND_DOCUMENT.md`

## Document Map

### `ARCHITECTURE_HANDOFF.md`

Implementation-oriented handoff document.

Contains:

- what has already been decided
- what remains unspecified
- what should be implemented first
- rules another agent should preserve

### `architecture/ARCHITECTURE.md`

High-level target architecture for the platform.

Contains:

- architectural layers
- deployment model
- provider isolation
- Unit of Work guidance
- Dependency Injection guidance
- stable application contracts

### `architecture/DOMAIN_MODEL.md`

DDD-focused domain modeling document.

Contains:

- bounded contexts
- ubiquitous language
- aggregates
- use cases
- DDD interpretation
- Unit of Work usage in application flow

### `architecture/TESTING_STRATEGY.md`

Testing and TDD document.

Contains:

- `pytest` as the standard framework
- fake-first testing policy
- use case and domain testing rules
- Unit of Work testing guidance

### `product/BACKGROUND_DOCUMENT.md`

Product and market rationale.

Contains:

- project vision
- why side-by-side comparison matters
- strategic positioning for the viewer SDK

## Important Rules Preserved Across Documents

- Use DDD in a pragmatic style
- Organize the application layer around explicit use cases
- Use `pytest` as the test framework
- Prefer fakes over mocks
- Use Unit of Work at application boundaries
- Use Litestar DI at the controller/handler boundary
- Keep the domain model framework-agnostic
- Keep providers isolated from each other
- Use one stable frontend contract: `RenderDocument`

### `specs/RENDER_DOCUMENT_SCHEMA.md`

Normalized frontend contract schema.

Contains:

- RenderDocument, RenderPage, RenderBlock, RenderTable, RenderCell, RenderFigure models
- coordinate system definition
- block type enum
- invariants and validation rules

### `specs/PROVIDER_CONTRACT.md`

Provider adapter interface specification.

Contains:

- ProviderAdapter abstract interface
- input/output/error contracts
- normalizer contract
- provider registry definition
- registered providers (Docling, OpenDataLoader)

### `specs/API_SPEC.md`

HTTP API specification.

Contains:

- document upload and retrieval endpoints
- analysis run creation and status endpoints
- comparison session endpoints
- provider listing endpoint
- error response format

### `specs/PERSISTENCE_MODEL.md`

Database and storage design.

Contains:

- PostgreSQL table definitions
- entity-relationship diagram
- artifact storage model
- migration strategy

### ADRs (`adr/`)

Architecture Decision Records.

- `0001` - Use DDD with explicit use cases
- `0002` - Use Unit of Work at application boundaries
- `0003` - Use Litestar DI only at the edge
- `0004` - Use RenderDocument as the frontend contract
- `0005` - Isolate providers by runtime
