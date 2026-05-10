# ADR 0004: Use RenderDocument as the Frontend Contract

## Status

Accepted

## Context

Different document analysis providers return different output structures. Docling returns a `DoclingDocument`. OpenDataLoader returns its own JSON format. Future providers will have their own schemas with different coordinate systems, block types, and nesting.

If the frontend consumes provider-native JSON directly:

- the viewer breaks every time a provider changes its output format
- comparison across providers requires the frontend to understand N different schemas
- adding a new provider requires frontend changes
- there is no consistent coordinate system for overlay rendering

## Decision

The frontend consumes exactly one schema: `RenderDocument`. Provider-native output is never sent to the frontend.

Each provider has a normalizer function that converts its raw output into a `RenderDocument`. The normalizer:

- normalizes all coordinates to `[0, 1]` top-left origin
- maps provider-specific block types to the canonical block type enum
- extracts tables, figures, and reading order into the standard structure
- attaches provider metadata for provenance

The `RenderDocument` schema is defined in `docs/specs/RENDER_DOCUMENT_SCHEMA.md` and implemented as Pydantic v2 models in `src/app/infrastructure/render_document.py`.

## Consequences

- The viewer and comparison UI depend on one stable schema, not N provider schemas
- Adding a provider requires writing a normalizer, not modifying the frontend
- Provider output format changes are absorbed by the normalizer without affecting the UI
- All coordinates are in the same system, so overlays align correctly across providers in side-by-side comparison
- Raw provider output is still stored and available via API for debugging, but the frontend never renders it directly
- Normalizer correctness is critical: schema violations will cause viewer errors, so contract tests are required for every normalizer
