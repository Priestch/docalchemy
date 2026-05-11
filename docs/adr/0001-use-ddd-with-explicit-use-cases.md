# ADR 0001: Use DDD with Explicit Use Cases

## Status

Accepted

## Context

The project is growing from a single-provider upload app into a multi-provider document analysis platform. The domain has clear bounded areas: documents, analysis runs, providers. The orchestration across these areas will become more complex as providers are added.

We need an architectural approach that:
- keeps the core domain model stable as infrastructure changes
- makes business rules explicit and testable
- avoids scattering orchestration logic across controllers and workers
- scales to multiple providers without coupling

## Decision

We use Domain-Driven Design in a pragmatic style, with an application layer organized around explicit use cases.

This means:

- **Bounded contexts** for major domain areas (documents, analysis, providers)
- **Explicit aggregates** for core lifecycle entities (SourceDocument, AnalysisRun)
- **Repositories** at aggregate boundaries
- **Domain rules** live inside the domain model, not in controllers or services
- **Application use cases** orchestrate across aggregates and infrastructure ports
- **Controllers and workers** call use cases; they do not contain business logic

We avoid:

- ceremony-heavy DDD that pushes all orchestration into aggregates
- generic service classes that accumulate unrelated behavior
- anemic domain models where entities are just data holders

## Consequences

- Adding a new provider or workflow means adding a new use case or adapter, not modifying existing orchestration code
- Business rules are unit-testable through domain entities and use cases with fake dependencies
- The domain model stays framework-agnostic (no Litestar, no SQLAlchemy imports in domain code)
- New contributors can understand behavior by reading use case files rather than tracing through controllers and callbacks
- There is a small amount of structural boilerplate (DTOs, repository interfaces, UoW interfaces) that a simpler architecture would not require
