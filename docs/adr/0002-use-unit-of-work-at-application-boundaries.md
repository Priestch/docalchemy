# ADR 0002: Use Unit of Work at Application Boundaries

## Status

Accepted

## Context

Application use cases need to coordinate repository access and persistence in a transactionally consistent way. Without a defined boundary, transaction management leaks into controllers, workers, or gets handled inconsistently.

Analysis runs are long-running asynchronous operations. If we hold a database transaction open for the entire duration of a provider execution, we exhaust connections and risk stale locks.

## Decision

Each application use case executes inside one Unit of Work. The Unit of Work:

- provides repository access for the bounded context
- defines the transaction boundary (commit on success, rollback on failure)
- commits durable domain changes once the use case completes

For asynchronous workflows (provider execution), the pattern is:

1. A synchronous use case creates/updates state inside one Unit of Work, then commits
2. A job is dispatched after commit
3. The worker handling that job opens its own Unit of Work for its own state changes

We use bounded Unit of Work types rather than one application-wide UoW:

- `DocumentsUnitOfWork` for document-related use cases
- `AnalysisUnitOfWork` for analysis run use cases
- `ComparisonUnitOfWork` for comparison session use cases

Non-transactional dependencies (object storage, queue publishers, provider clients) stay outside the Unit of Work and are injected into use cases separately.

## Consequences

- Transaction scope is always explicit and tied to a use case boundary
- Long-running provider execution never holds a database connection
- Use case tests can use a simple fake UoW without booting a real database
- Each bounded UoW exposes only the repositories relevant to its context, avoiding a global dependency bucket
- Workers are responsible for opening their own UoW, which means state updates from async work are independently testable
