# Domain Model

## Purpose

This document defines the Domain-Driven Design approach for the project. It describes the bounded contexts, ubiquitous language, core aggregates, and the use case-oriented application layer.

The project should use lightweight, pragmatic DDD. The goal is clarity and maintainability, not ceremony.

## DDD Style

The project should use:

- bounded contexts for major problem areas
- explicit aggregates for core lifecycle entities
- repositories at aggregate boundaries
- domain rules inside the domain model
- application use cases for orchestration

The project should avoid:

- putting queue logic into the domain model
- putting storage adapters into the domain model
- putting provider SDK code into the domain model
- turning every DTO into a rich domain object without need

## Ubiquitous Language

The following terms should be used consistently.

### SourceDocument

The original uploaded file that acts as the baseline for all analysis and comparison.

### AnalysisRun

One provider's attempt to analyze one source document.

### Provider

A document analysis engine integrated into the platform through a narrow adapter and isolated runtime.

### AnalysisArtifact

Any stored output produced by an analysis run, such as raw provider output or normalized render output.

### RenderDocument

The normalized application-owned representation of a provider result used by the frontend viewer and comparison UI.

### ComparisonSession

A user-facing grouping that compares multiple analysis runs on the same source document.

## Bounded Contexts

The system should be modeled around the following bounded contexts.

### Documents Context

Owns:

- source document lifecycle
- upload metadata
- source storage reference
- document retrieval

Primary concepts:

- `SourceDocument`

### Analysis Context

Owns:

- analysis run lifecycle
- status transitions
- retry rules
- provider assignment
- execution metadata

Primary concepts:

- `AnalysisRun`
- `AnalysisArtifact`

### Provider Registry Context

Owns:

- provider definitions
- provider capabilities
- provider runtime targets
- provider configuration schemas

Primary concepts:

- `ProviderDefinition`

### Comparison Context

Owns:

- compare session composition
- multi-run loading
- comparison state

Primary concepts:

- `ComparisonSession`

### Benchmark Context

Optional later.

Owns:

- datasets
- labels
- scores
- evaluation reports

This context must remain distinct from comparison. Comparison is qualitative product workflow. Benchmarking is quantitative evaluation workflow.

## Core Aggregates

### SourceDocument Aggregate

Responsibilities:

- represent the uploaded source file
- hold canonical metadata
- enforce basic identity and integrity rules

Suggested invariants:

- a source document must reference exactly one canonical stored file
- checksum and storage key must be present once persisted

### AnalysisRun Aggregate

Responsibilities:

- represent one provider run against one source document
- own lifecycle state
- record provider identity and config snapshot
- reference generated artifacts

Suggested invariants:

- one analysis run belongs to exactly one source document
- an analysis run must have exactly one provider
- terminal states are immutable except through explicit retry behavior

Suggested states:

- `PENDING`
- `QUEUED`
- `RUNNING`
- `SUCCESS`
- `FAILED`
- `CANCELLED`

### ComparisonSession Aggregate

Responsibilities:

- represent a user-visible comparison between multiple analysis runs
- ensure all compared runs reference the same source document

Suggested invariants:

- every run in a comparison session must belong to the same source document
- a comparison session must contain at least two runs to be meaningful

## Domain vs Application Responsibilities

The domain layer should own:

- entity identity
- state transitions
- invariants
- domain events where needed
- core business meaning

The application layer should own:

- use case execution
- transactions
- orchestration across aggregates
- calling repositories and gateways
- queue dispatch
- artifact persistence coordination

The infrastructure layer should own:

- database adapters
- object storage adapters
- queue adapters
- provider SDK adapters
- external service communication

## Dependency Injection in DDD Terms

Dependency Injection should support the boundary between application logic and infrastructure, while keeping the domain model pure.

The expected rule is:

- domain entities and value objects must not resolve dependencies
- use cases receive dependencies explicitly
- frameworks and infrastructure compose those dependencies at the edge

Litestar DI may be used at controller and handler boundaries, but the domain model must remain unaware of Litestar itself.

## Unit Of Work in DDD Terms

Unit of Work belongs at the application and infrastructure boundary, not inside the domain model itself.

Its role is to coordinate repository access and persistence for aggregates participating in a use case.

The expected relationship is:

- aggregates enforce rules
- repositories load and persist aggregates
- Unit of Work defines the transaction boundary around the use case

This means the domain model should not depend directly on Unit of Work APIs. Application use cases should depend on Unit of Work and repositories.

The Unit of Work may expose repositories directly, which is a reasonable pattern for this project, provided that the Unit of Work remains bounded to a coherent context and does not become a global dependency bucket.

## Use Cases

The application layer should be organized around use cases, not around generic service classes.

Recommended use cases:

- `UploadSourceDocument`
- `CreateAnalysisRun`
- `CreateComparisonRunSet`
- `DispatchAnalysisRun`
- `MarkAnalysisRunRunning`
- `MarkAnalysisRunSucceeded`
- `MarkAnalysisRunFailed`
- `CreateComparisonSession`
- `GetComparisonSession`
- `GetRenderDocument`
- `RetryAnalysisRun`

Each use case should define:

- input DTO
- output DTO
- dependencies
- transaction boundary
- emitted events if any

Each use case should generally execute inside one Unit of Work.

That Unit of Work should:

- provide repository access
- control commit and rollback
- define when domain changes become durable

Use cases may also depend on non-transactional ports, such as provider registries or job dispatchers, but these should normally be injected separately from the Unit of Work.

## Use Case Examples

### UploadSourceDocument

Responsibilities:

- accept upload input
- validate file metadata
- store source file
- create `SourceDocument`

Does not own:

- provider dispatch
- comparison logic

### CreateAnalysisRun

Responsibilities:

- validate provider choice
- create `AnalysisRun`
- store requested config snapshot

Does not own:

- actual provider execution

### DispatchAnalysisRun

Responsibilities:

- load run metadata
- resolve provider runtime target
- enqueue the work
- move the run to queued state

Unit of Work guidance:

- update run state and persist queueing metadata inside the Unit of Work
- do not execute provider analysis itself inside that same Unit of Work

### MarkAnalysisRunSucceeded

Responsibilities:

- attach artifact references
- transition run to success
- record completion metadata

This use case should open its own Unit of Work when processing a worker result.

### CreateComparisonSession

Responsibilities:

- validate that all selected runs belong to the same source document
- create a comparison session

## Domain Events

Domain events may be introduced where they help decouple behavior cleanly.

Potential events:

- `SourceDocumentUploaded`
- `AnalysisRunCreated`
- `AnalysisRunQueued`
- `AnalysisRunSucceeded`
- `AnalysisRunFailed`

These events should communicate domain facts. They should not be used as a vague replacement for application orchestration.

## Repository Boundaries

Repositories should exist at aggregate boundaries.

Recommended repositories:

- `SourceDocumentRepository`
- `AnalysisRunRepository`
- `ComparisonSessionRepository`
- `ProviderRegistryRepository` or provider registry service abstraction

Repositories should return domain objects or aggregate-root-oriented representations, not provider SDK models.

Repositories used by a use case should normally be obtained through the Unit of Work abstraction so transaction scope stays explicit.

This is the preferred style for this project:

- handlers receive use cases through Litestar DI
- use cases receive a Unit of Work and other required ports
- the Unit of Work exposes the repositories needed for that use case context

## Domain Rules To Preserve

The model should preserve these core rules:

- the source document is the baseline artifact
- one source document can have many analysis runs
- one analysis run belongs to one provider
- raw provider output is never the frontend contract
- comparison sessions compare runs on the same source document only

## Modeling Guidance

Prefer a small number of important domain concepts over many shallow abstractions.

Start with:

- `SourceDocument`
- `AnalysisRun`
- `ComparisonSession`
- `RenderDocument` as an application-owned contract

Do not over-model provider internals into the core domain.

Providers are integrations. The core product domain is the workflow around source documents, runs, and comparison.

## Use Case and Unit Of Work Rule

The default rule for this project is:

- one use case
- one Unit of Work
- one explicit commit boundary

Exceptions should be rare and justified by a clear technical requirement.

Related DI rule:

- use case dependencies should be explicit
- domain dependencies should not be looked up dynamically
- repository access should normally flow through the Unit of Work
