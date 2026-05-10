# Architecture Document

## Title

Architecture for a Multi-Provider Document Analysis Comparison Platform

## Purpose

This document defines the target architecture for the project as a document analysis platform with a PDF viewer and comparison product on top.

The primary goals are:

- support multiple document analysis providers cleanly
- isolate provider-specific dependencies and failures
- normalize provider results into one stable application-owned model
- render and compare multiple provider outputs on the same source document
- provide a strong foundation for product growth, operational reliability, and industry positioning

## Architectural Style

The project should use Domain-Driven Design in a pragmatic style, with explicit application use cases and a test-driven engineering workflow.

This means:

- the domain model should express the core business concepts clearly
- application behavior should be organized around use cases
- infrastructure concerns should remain outside the domain model
- domain behavior should be developed with a test-first mindset where practical

Companion documents:

- `docs/architecture/DOMAIN_MODEL.md`
- `docs/architecture/TESTING_STRATEGY.md`
- `docs/product/BACKGROUND_DOCUMENT.md`

## System Vision

The system should let a user upload one document, run multiple document analysis providers against it, and inspect the results side by side in a PDF viewing experience. The source document is the baseline, and provider outputs are rendered as overlays or structured views on top of that baseline.

The system is not only a viewer and not only an analyzer. It combines:

- document ingestion
- analysis orchestration
- provider execution
- normalization
- visual comparison

## Core Architectural Principle

The platform should own three stable concepts:

- `SourceDocument`
- `AnalysisRun`
- `RenderDocument`

Everything else may vary across providers, runtimes, or deployments.

## Dependency Injection

The project should enforce Dependency Injection as an architectural rule.

DI should occur at system boundaries and in the application layer, not inside the domain model.

Recommended rule:

- framework DI at the controller, handler, CLI, and worker entrypoint level
- explicit dependency injection into use cases
- infrastructure wiring at the composition root
- no service locator pattern inside domain or application code

For the web layer, Litestar's DI system should be used at controller and handler boundaries.

That means:

- Litestar resolves use cases or dependency providers at the edge
- handlers call use cases
- use cases depend on abstractions such as Unit of Work, registries, and gateways
- domain entities and value objects remain framework-agnostic

## Architectural Layers

### 1. Source Document Platform

Responsibilities:

- accept uploads
- validate file metadata
- store source documents
- manage document metadata
- expose source file retrieval

### 2. Analysis Orchestration Layer

Responsibilities:

- create analysis runs
- select providers
- dispatch jobs
- manage timeouts and retries
- update run state
- record provider metadata and runtime metadata

### 3. Provider Runtime Layer

Responsibilities:

- execute one provider's analysis logic
- manage provider-specific dependencies
- produce provider-native raw output
- optionally produce normalized output

### 4. Normalization and Render Layer

Responsibilities:

- convert raw provider output into an application-owned render model
- standardize coordinates, page mapping, block types, and structure
- prepare results for UI rendering and comparison

### 5. Viewer and Comparison Layer

Responsibilities:

- render the source document
- render provider overlays
- compare multiple providers side by side
- synchronize page, zoom, and scroll
- support qualitative evaluation workflows

## DDD Interpretation

The system should use DDD mainly for the core product model and bounded context boundaries, not as a ceremony-heavy modeling exercise.

DDD should be applied to:

- ubiquitous language
- bounded contexts
- aggregate boundaries
- domain rules and invariants
- domain events where needed

DDD should not be used to force all orchestration logic into aggregates.

## Use Case-Oriented Application Layer

The application layer should be organized around explicit use cases.

Examples:

- `UploadSourceDocument`
- `CreateAnalysisRun`
- `CreateComparisonRunSet`
- `DispatchAnalysisRun`
- `MarkAnalysisRunSucceeded`
- `MarkAnalysisRunFailed`
- `GetComparisonSession`
- `GetRenderDocument`
- `RetryAnalysisRun`

Controllers and async handlers should call use cases. They should not contain core orchestration logic directly.

## Unit Of Work

The project should use a Unit of Work pattern at the application boundary.

Unit of Work is an application and infrastructure coordination pattern, not a domain concept. Its role is to provide a transactional boundary around a use case and coordinate repository persistence consistently.

The expected rule is:

- one application use case should generally execute inside one Unit of Work

The Unit of Work may expose repositories as attributes or properties, but only for repositories relevant to the bounded context or workflow it coordinates.

The Unit of Work should:

- load repositories needed by the use case
- track changes to aggregates through repositories
- commit successful changes once the use case completes
- roll back changes if the use case fails

Unit of Work should not:

- contain core business rules itself
- run long provider analysis jobs inside one open transaction
- become a generic service locator for unrelated concerns

Preferred approach:

- use bounded-context or workflow-oriented Unit of Work types
- expose only the repositories needed for that context

Examples:

- `DocumentsUnitOfWork`
- `AnalysisUnitOfWork`
- `ComparisonUnitOfWork`

Non-transactional dependencies should usually stay outside the Unit of Work:

- object storage gateways
- queue publishers
- provider runtime clients
- external HTTP clients

## Top-Level Domains

The system should be designed around these domains:

- `documents`
- `analysis`
- `providers`
- `normalization`
- `comparison`
- later `benchmark`

## Core Entities

### SourceDocument

Represents the original uploaded file.

Recommended fields:

- `id`
- `name`
- `mime_type`
- `size`
- `storage_key`
- `checksum`
- `uploaded_by`
- `created_at`

### AnalysisRun

Represents one provider analyzing one source document.

Recommended fields:

- `id`
- `source_document_id`
- `provider`
- `provider_version`
- `status`
- `requested_config`
- `runtime_metadata`
- `started_at`
- `finished_at`
- `error_code`
- `error_message`

### AnalysisArtifact

Represents stored outputs related to an analysis run.

Recommended fields:

- `id`
- `analysis_run_id`
- `artifact_type`
- `format`
- `storage_key`
- `created_at`

### ComparisonSession

Represents a user-facing comparison grouping.

Recommended fields:

- `id`
- `source_document_id`
- `analysis_run_ids`
- `created_by`
- `created_at`

## Stable Application Contracts

The system should define stable contracts at the platform boundary:

- `SourceDocument`
- `AnalysisRun`
- `RenderDocument`

## RenderDocument Model

`RenderDocument` is the application-owned schema consumed by the viewer and comparison UI.

Suggested structure:

- `document`
- `pages`
- `blocks`
- `tables`
- `cells`
- `figures`
- `spans`
- `reading_order`
- `confidence`
- `provider_annotations`

The viewer should consume only `RenderDocument`, never provider-native output.

## Provider Architecture

Each provider should be implemented as a narrow adapter.

Each provider must define:

- `provider_id`
- `version`
- `capabilities`
- `configuration schema`
- `execution entrypoint`

Providers should not own:

- application APIs
- comparison logic
- viewer logic
- global orchestration rules

## Provider Registry

The system should contain a provider registry owned by the platform.

The registry should define:

- provider name
- runtime target
- capabilities
- supported formats
- configuration schema
- timeout policy
- retry policy

## Deployment Model

The recommended deployment model is a control plane plus worker plane.

### Control Plane

The control plane owns:

- API service
- frontend static app or frontend host
- metadata database
- orchestration rules
- provider registry
- compare session APIs

### Worker Plane

The worker plane owns:

- provider-specific workers
- normalization jobs if separated
- queue consumers
- heavy compute tasks

## Recommended Runtime Units

- `api-service`
- `web-frontend`
- `orchestrator-worker`
- `provider-docling-worker`
- `provider-provider-x-worker`
- `provider-provider-y-worker`
- `postgres`
- `redis` or equivalent broker
- `object-storage`

## Why Provider Isolation Is Required

Provider isolation is required because document analysis providers often differ in:

- Python dependencies
- system libraries
- OCR runtimes
- GPU requirements
- memory profiles
- startup behavior

Each provider should therefore have:

- its own container image
- its own dependency lockfile
- its own environment variables
- its own queue
- its own scaling policy

## Communication Model

The system should use a mixed communication model.

### Synchronous HTTP

Used for:

- uploads
- metadata queries
- run status queries
- render artifact retrieval
- comparison session creation

### Asynchronous Jobs

Used for:

- provider execution
- heavy analysis
- optional normalization
- retries and delayed processing

### Shared Artifact Storage

Used for:

- source documents
- raw provider outputs
- normalized outputs
- render outputs

Large artifacts should be passed by storage reference, not embedded in queues or relational database rows.

## Unit Of Work and Asynchronous Execution

Because analysis execution is asynchronous and potentially slow, Unit of Work boundaries must remain short-lived.

Recommended pattern:

- a synchronous API use case creates a document or analysis run inside one Unit of Work
- the Unit of Work commits
- an event or job is dispatched after commit
- the worker handling that job opens its own Unit of Work
- the worker updates run state and artifacts inside that worker-local Unit of Work

## Queue Model

The system should use provider-specific queues.

Examples:

- `analysis.docling`
- `analysis.provider_x`
- `analysis.provider_y`

## Storage Model

Two storage classes are required.

### Metadata Storage

Recommended technology:

- PostgreSQL

### Artifact Storage

Recommended technology:

- S3-compatible object storage, GCS, or MinIO

For local development, the filesystem may stand in for object storage.

## DI at the Web Boundary

For HTTP requests, Litestar DI should be the default mechanism for wiring handlers to application dependencies.

Recommended flow:

- Litestar resolves a use case or use case dependencies
- the handler remains thin
- the handler delegates to the use case
- the use case coordinates Unit of Work and other ports

## Comparison Product Model

Comparison is a first-class product feature.

For one source document, the system should support multiple runs and multiple visible panes. Each pane should use the same source file and a different `RenderDocument`.

The comparison UI should support:

- side-by-side panes
- synchronized page, zoom, and scroll
- block overlays
- table overlays
- reading order overlays
- visibility toggles
- loading states for incomplete runs

## Design Constraints

The system should satisfy the following constraints:

- adding a provider should not require changing viewer internals
- adding a provider should not require redesigning core APIs
- provider raw outputs should remain available for debugging
- the viewer should consume only normalized render output
- one source document can have many analysis runs
- one provider failure must not break the platform

## Architecture Decision Summary

The key architectural decisions are:

1. Separate source document storage from analysis execution
2. Introduce `AnalysisRun` as a first-class entity
3. Define `RenderDocument` as the stable frontend contract
4. Isolate providers into independent runtimes
5. Use provider-specific queues
6. Store artifacts in object storage, not only in the database
7. Keep comparison and benchmarking as separate product concerns
8. Use Litestar DI at the edge
9. Use Unit of Work at application boundaries

## Recommended Implementation Order

1. Define core entities and state model
2. Define `RenderDocument`
3. Define provider contract and registry
4. Define orchestration flow and queue topology
5. Define artifact storage model
6. Define comparison API and session model
7. Build provider runtimes
8. Build compare UI

## Final Architecture Goal

The architecture should make the following statement true:

One source document can be analyzed by many providers, each provider can run and evolve independently, and the product can compare their outputs visually through one stable render contract.
