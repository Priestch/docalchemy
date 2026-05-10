# ADR 0003: Use Litestar DI Only at the Edge

## Status

Accepted

## Context

The project uses Litestar as its web framework. Litestar provides a dependency injection system for resolving request-scoped and application-scoped dependencies in controllers and handlers.

If framework DI is used throughout the application and domain layers, those layers become coupled to Litestar. This makes domain and application code harder to test, harder to reuse in worker processes, and harder to reason about in isolation.

## Decision

Litestar DI is used exclusively at the web boundary: controllers and handlers. The domain and application layers remain framework-agnostic.

The wiring flow is:

1. Litestar resolves a use case (or its dependencies) via DI at the controller/handler level
2. The handler calls the use case
3. The use case receives its dependencies explicitly through constructor parameters (UoW, registries, gateways)
4. Domain entities and value objects have no framework imports

For worker entrypoints (Celery tasks), manual construction replaces Litestar DI since workers run outside the web request lifecycle.

## Consequences

- Domain and application code can be tested by instantiating use cases directly with fake dependencies, no Litestar boot required
- The same use cases can be called from HTTP handlers, CLI commands, or Celery workers without modification
- Litestar-specific code is confined to the `server/` and `domain/*/controllers.py` and `domain/*/dependencies.py` files
- If the web framework ever changes, only the edge layer needs to be rewritten
- There is some manual wiring in worker entrypoints that a full-framework DI approach would avoid, but this is an acceptable tradeoff for keeping the core portable
