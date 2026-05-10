# Testing Strategy

## Purpose

This document defines the testing strategy for the project and explains how Test-Driven Development should be applied.

The system should use TDD pragmatically, especially for domain logic and use case behavior. The goal is to make behavior explicit, keep the design clean, and reduce regressions as the architecture grows.

The project should use `pytest` as the primary test framework.

## TDD Policy

The preferred workflow is:

1. write a failing test for the intended behavior
2. implement the smallest change that makes the test pass
3. refactor while keeping tests green

This is most important for:

- domain rules
- aggregate state transitions
- use case behavior
- normalization logic
- provider contracts

It is less important to force strict test-first sequencing for:

- trivial wiring
- purely mechanical configuration
- one-off operational scripts

## Test Framework

The project should use `pytest` as the standard test framework for all test layers.

This applies to:

- domain tests
- use case tests
- contract tests
- integration tests
- end-to-end tests where practical

Reasons:

- simple fixture model
- strong ecosystem
- readable tests
- good support for parametrization
- good fit for fake-based testing

Alternative frameworks should not be introduced unless there is a clear technical need.

## Test Double Policy

The project should prefer fakes over mocks.

Priority order:

1. real domain objects
2. fakes
3. stubs if needed
4. mocks only when interaction verification is truly necessary

Reasons:

- fakes make tests easier to read
- fakes reduce coupling to implementation details
- fakes encourage testing behavior rather than call structure
- fake-based tests survive refactoring better than mock-heavy tests

Mocks should be treated as an exception, not the default style.

Good uses of fakes in this project:

- fake repositories
- fake queue gateways
- fake object storage gateways
- fake provider registry adapters
- fake provider runtimes for use case tests

Mocks should be reserved for rare cases where verifying an external interaction contract is the actual behavior under test.

This fake-first policy is enabled by explicit dependency injection and by use cases depending on ports such as Unit of Work, registries, and gateways.

## Test Layers

The project should use multiple test layers.

### 1. Domain Unit Tests

Focus:

- aggregate invariants
- state transitions
- value object behavior
- domain rule enforcement

Examples:

- `AnalysisRun` cannot move from `FAILED` to `SUCCESS` without retry
- `ComparisonSession` cannot include runs from different source documents

These tests should be fast and isolated.

### 2. Use Case Tests

Focus:

- application behavior
- repository interactions
- orchestration logic
- emitted events and side effects

Examples:

- `CreateAnalysisRun` stores provider config snapshot
- `DispatchAnalysisRun` places work on the correct provider queue
- `CreateComparisonSession` rejects mixed-document run sets

These tests should use fake repositories and gateways by default.

They should also use a fake Unit of Work by default.

### 3. Contract Tests

Focus:

- provider adapter compliance
- normalization output shape
- storage gateway behavior
- queue adapter behavior

Examples:

- every provider returns required metadata and raw output
- every normalizer produces valid `RenderDocument`

These tests make it safer to add new providers.

Where possible, contract tests should run against reusable fake implementations first, then against real adapters in integration tests.

### 4. Integration Tests

Focus:

- database repository behavior
- object storage integration
- queue integration
- API to use case wiring

These tests should verify that real adapters work together correctly.

Integration tests should include transactional behavior around the real Unit of Work implementation.

### 5. End-to-End Tests

Focus:

- upload -> analysis run -> render result -> compare view flow

These tests should be limited in number and focus on the highest-value user flows.

## Testing Priorities

Highest priority:

- domain rules
- use cases
- provider contract tests
- normalization tests

Medium priority:

- repository integration
- API integration

Lower priority:

- thin controller glue
- framework boilerplate

## Pytest Conventions

The project should use `pytest` conventions consistently.

Recommended practices:

- use plain `assert`
- prefer fixtures for reusable setup
- use parametrization for provider and render-schema variations
- keep test setup small and local unless sharing adds clarity
- avoid class-based tests unless they add real structure

Tests should read as executable specifications of behavior rather than framework-heavy test code.

## Unit Of Work Testing Guidance

Use case tests should prefer a fake Unit of Work implementation.

The fake Unit of Work should make it easy to verify:

- which repositories were involved
- whether commit occurred
- whether rollback occurred on failure

This fits the fake-first policy and keeps tests behavior-focused.

Fake repositories may be exposed through the fake Unit of Work in the same way real repositories are exposed through the production Unit of Work implementation.

Real Unit of Work implementations should be covered by integration tests to verify:

- transaction boundaries
- persistence semantics
- rollback behavior
- interaction with repository implementations

## Provider Test Expectations

Every provider integration should pass a shared provider contract suite.

Each provider should prove:

- supported input types are declared correctly
- execution returns raw output
- provider metadata is present
- failures are mapped to platform error behavior consistently

Each provider should also be tested against a shared document fixture set where practical.

Provider use case tests should prefer fake provider adapters. Real provider runtimes belong in contract or integration tests, not in the default fast test path.

## RenderDocument Validation

The normalized `RenderDocument` contract is a central stability boundary and should be tested directly.

Tests should validate:

- required fields are present
- page indices are valid
- coordinates are normalized consistently
- block and table structures are usable by the frontend

The frontend should never become the first place where schema errors are discovered.

## TDD and DDD Relationship

DDD defines how the system is modeled.
TDD defines how those models and use cases are developed safely.

The strongest TDD targets in this project are:

- domain aggregates
- use cases
- provider contract adapters
- normalization logic

This is where test-first development adds the most architectural value.

## Suggested Test Organization

Suggested structure:

- `tests/domain/`
- `tests/application/`
- `tests/contracts/`
- `tests/integration/`
- `tests/e2e/`

This structure should mirror the intended architecture rather than the current framework layout.

Common fake implementations should live in a shared test support area such as:

- `tests/fakes/`
- `tests/fixtures/`

This shared area should include fake Unit of Work implementations for application-layer tests.

This should make fake-first testing easy and conventional.

## Merge Expectations

Behavioral changes should include tests.

At minimum:

- new domain behavior should have domain or use case tests
- new provider integrations should include contract tests
- changes to `RenderDocument` should include normalization tests
- critical user flows should retain end-to-end coverage

Tests added for new behavior should prefer fake-based designs over mock-driven designs unless there is a documented reason not to.

## Practical Guidance

Use TDD aggressively where design is being discovered.

This is especially useful for:

- aggregate rules
- run lifecycle
- comparison validation
- normalization edge cases

Do not use tests as a substitute for architecture. Tests are most effective when the domain boundaries and use cases are already clear.

Litestar DI should not need to be booted for the default unit and use case test path. Most tests should instantiate use cases directly with fake Unit of Work and fake ports.

## Enforcement Guidance

The default expectation for contributors is:

- use `pytest`
- write behavior-focused tests
- prefer fakes over mocks
- avoid verifying internal call sequences unless necessary

If a test uses mocks heavily, the author should be able to justify why a fake would not work better for that case.
