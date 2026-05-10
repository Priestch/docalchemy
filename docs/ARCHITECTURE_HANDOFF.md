# Architecture Handoff

## Purpose

This document is the implementation handoff for another coding agent.

It summarizes:

- the decisions already made
- the non-negotiable architectural rules
- the major missing specifications
- the recommended implementation order

This document is the fastest entry point for continuing the work.

## What Has Already Been Decided

The project should be built as a multi-provider document analysis comparison platform with a PDF viewer product on top.

The system is not just:

- a PDF viewer
- a document upload app
- a single-provider analysis pipeline

The system should support:

- one source document
- many analysis runs
- many providers
- one normalized render contract
- side-by-side visual comparison in the viewer

## Architectural Rules

These rules should be preserved.

### 1. Use DDD Pragmatically

The project should use:

- bounded contexts
- explicit aggregates
- explicit use cases
- repositories at aggregate boundaries

The project should avoid ceremony-heavy DDD that pushes orchestration logic into the domain unnecessarily.

### 2. Use Cases Are the Application Entry Model

Controllers and async handlers should call use cases.

The application layer should be organized around explicit use cases such as:

- `UploadSourceDocument`
- `CreateAnalysisRun`
- `DispatchAnalysisRun`
- `MarkAnalysisRunSucceeded`
- `CreateComparisonSession`
- `GetRenderDocument`

### 3. Use Unit of Work at Application Boundaries

Use cases should generally execute inside one Unit of Work.

Unit of Work:

- coordinates repositories
- defines transaction boundaries
- commits durable domain changes

Unit of Work should not:

- contain business rules
- become a global service locator
- hold unrelated infrastructure dependencies

### 4. Use Litestar DI at the Edge

Litestar DI should be used at:

- controllers
- handlers
- worker entrypoint wiring if useful

The domain model must remain unaware of Litestar.

### 5. Prefer Bounded Unit of Work Types

It is acceptable for Unit of Work to expose repositories directly, but only within a coherent context.

Good examples:

- `DocumentsUnitOfWork`
- `AnalysisUnitOfWork`
- `ComparisonUnitOfWork`

Avoid one giant application-wide Unit of Work.

### 6. Use `pytest` and Prefer Fakes Over Mocks

The testing policy is:

- `pytest` is the standard framework
- prefer fakes over mocks
- use fake Unit of Work and fake repositories in use case tests
- reserve mocks for rare interaction-verification cases

### 7. Keep Providers Isolated

Providers are integrations, not the core domain.

Providers should be isolated by runtime when necessary because dependencies may conflict.

The target deployment should support separate provider workers or services.

### 8. The Frontend Contract Must Be Stable

The frontend must not consume provider-native JSON directly.

The system should define one application-owned render contract:

- `RenderDocument`

This is a core architectural boundary.

## Documents To Read

The supporting documents are:

- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/DOMAIN_MODEL.md`
- `docs/architecture/TESTING_STRATEGY.md`
- `docs/product/BACKGROUND_DOCUMENT.md`

## What Is Still Missing

The architecture is directionally defined, but several important specifications do not yet exist.

### 1. `RenderDocument` Schema

This is the most important missing spec.

It must define:

- pages
- blocks
- tables
- cells
- figures
- spans
- reading order
- coordinates
- confidence/provenance metadata

Without this, backend and frontend cannot align cleanly.

### 2. Provider Contract

Need an exact spec for:

- provider input
- provider output
- capabilities
- error model
- artifact expectations

### 3. API Spec

Need request/response definitions for:

- document upload
- analysis run creation
- render result retrieval
- comparison session creation

### 4. Persistence Model

Need concrete DB and storage design for:

- `SourceDocument`
- `AnalysisRun`
- `AnalysisArtifact`
- `ComparisonSession`

### 5. ADRs

Need architecture decisions recorded formally.

Recommended first ADRs:

- use DDD with explicit use cases
- use Unit of Work at application boundaries
- use Litestar DI only at the edge
- use `RenderDocument` as the frontend contract
- isolate providers by runtime

## Recommended Implementation Order

Another agent should follow this order:

1. Create `RENDER_DOCUMENT_SCHEMA.md`
2. Create `PROVIDER_CONTRACT.md`
3. Create `API_SPEC.md`
4. Create `PERSISTENCE_MODEL.md`
5. Create initial ADR set under `docs/adr/`
6. Define package layout matching the architecture
7. Implement `SourceDocument`, `AnalysisRun`, and `AnalysisArtifact`
8. Implement Unit of Work interfaces and fake implementations
9. Implement first use cases
10. Add one fake provider first
11. Add one real provider after contracts are stable

## Recommended First Vertical Slice

The first implementation slice should be intentionally narrow.

Suggested slice:

1. upload a source document
2. create one analysis run
3. return one fake `RenderDocument`
4. render it in a basic viewer page

Then expand to:

1. two providers
2. two runs on one source document
3. comparison session
4. side-by-side viewer panes

## Things Another Agent Should Not Do

- do not couple the frontend directly to provider-native output
- do not place provider SDK code inside the domain model
- do not build one giant Unit of Work
- do not rely on mocks as the default testing style
- do not put major orchestration logic in controllers
- do not run long provider analysis work inside one open DB transaction

## Target End State

The architecture should make the following statement true:

One source document can be analyzed by many providers, each provider can evolve independently, and the product can compare their outputs visually through one stable render contract.
