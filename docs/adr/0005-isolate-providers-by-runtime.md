# ADR 0005: Isolate Providers by Runtime

## Status

Accepted

## Context

Document analysis providers have conflicting dependencies:

- Different Python versions or incompatible library versions
- Different system-level requirements (Java runtime, Tesseract OCR, GPU drivers)
- Different memory profiles and startup costs
- Different failure modes that should not cascade to other providers

If all providers run in the same process or container:

- dependency conflicts require painful version pinning or workarounds
- one provider's crash or memory leak can take down other providers
- scaling one provider requires scaling all of them
- adding a provider with unusual system requirements blocks the entire deployment

## Decision

Each provider runs in its own isolated container with its own:

- Docker image and dependency lockfile
- Celery queue (e.g. `analysis.docling`, `analysis.opendataloader`)
- environment variables and configuration
- scaling and resource policy

The control plane dispatches work to provider-specific queues. Each provider worker:

1. pulls a job from its own queue
2. executes the provider adapter
3. saves raw artifacts via the shared storage service
4. runs the normalizer to produce a `RenderDocument`
5. updates analysis run state in the database

Provider adapters must not import domain entities, access the database directly, or depend on each other.

## Consequences

- Adding a provider means adding a new container image and queue, not modifying existing provider code
- Dependency conflicts between providers are impossible by construction
- One provider's failure does not affect other providers' availability
- Each provider can be scaled independently based on its actual load
- Deployment and CI complexity increases: each provider has its own build pipeline
- Local development requires either Docker Compose or a way to run a single provider at a time
