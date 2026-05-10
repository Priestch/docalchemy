# Background Document

## Title

Document Analysis Comparison Platform for a PDF Viewer SDK

## Summary

This project can evolve from a document upload and analysis app into a comparison platform for document analysis providers. The core idea is simple: run the same source document through multiple providers, normalize their outputs, and present the results side by side in a strong PDF viewing experience.

This direction serves two goals at the same time:

- Build a useful product for developers and teams evaluating document analysis quality.
- Use that product to promote the PDF viewer SDK and establish credibility in the document analysis industry.

## Background

Document analysis systems are difficult to evaluate. Different providers perform differently on OCR, layout, tables, reading order, multilingual documents, and scanned PDFs. Teams often compare outputs manually using scripts, JSON dumps, screenshots, or ad hoc demos. That workflow is fragmented and inefficient.

At the same time, PDF viewers are usually positioned as rendering components, not as inspection tools for document intelligence. This creates an opportunity: a viewer SDK can become the best interface for understanding, comparing, and trusting document analysis results.

## Problem

Teams evaluating document analysis providers face several issues:

- Provider outputs are inconsistent and difficult to compare directly.
- Raw JSON is hard to inspect visually.
- Layout quality is easier to judge visually than numerically, but tools for side-by-side inspection are weak.
- Benchmarking usually focuses on one provider at a time rather than comparative evaluation on the same file.
- There is no clear neutral UI layer that helps users understand why one provider is better or worse on a specific document.

## Opportunity

The project can fill this gap by becoming a provider-neutral document analysis comparison platform built around a strong PDF viewing experience.

The most valuable product idea is not just "viewer plus AI." The more distinctive idea is:

**A visual inspection and comparison layer for document analysis engines.**

This positions the product as infrastructure for evaluation, debugging, demos, and trust.

## Product Vision

Users upload one document, select multiple analysis providers, and see the results rendered side by side on top of the same source PDF. Each pane shows provider-specific overlays such as text blocks, tables, reading order, OCR regions, and extracted structure.

The viewer becomes the center of the experience:

- same source file in every pane
- synchronized page, zoom, and scroll
- toggles for raw vs normalized overlays
- visual diff of provider output
- shareable comparison sessions

## Why This Matters

This direction is useful both as a product and as a market position.

For the product:

- It helps teams choose providers more quickly.
- It helps engineers debug extraction failures.
- It makes qualitative evaluation practical.
- It creates a strong workflow around real documents, not just APIs.

For promotion:

- It gives the SDK a distinctive story.
- It makes demos easy to understand and share.
- It creates material for technical content, benchmark writeups, and case studies.
- It positions the author as someone who understands both document analysis and viewer UX.

## Target Users

- Teams evaluating OCR and document analysis providers
- Developers building document processing products
- AI engineers comparing extraction quality on real datasets
- Product teams needing a visual QA workflow
- Solution architects choosing between vendors or open source tools

## Product Principles

- Provider-neutral by design
- One stable render schema owned by the application
- Original source document is always the visual baseline
- Side-by-side comparison is qualitative first
- Objective scoring can be added later
- Provider integrations should be isolated and replaceable

## Scope

### In Scope

- Upload a document once
- Run multiple providers on the same source file
- Store raw provider outputs
- Normalize outputs into an app-owned render schema
- Render provider overlays side by side in the viewer
- Track run status, provider name, version, config, and latency

### Out of Scope For Initial Version

- Full objective precision benchmarking with gold labels
- Automated leaderboards
- Provider-specific downstream business workflows
- Deep annotation tooling

## Architecture Direction

The architecture should be based on four layers:

1. Ingestion
   Owns file upload and source file storage.

2. Orchestration
   Owns provider selection, job dispatch, retries, run status, and result tracking.

3. Provider runtimes
   Each provider performs document analysis with its own dependencies and config.

4. Normalization and rendering
   Converts provider output into a single render schema consumed by the frontend.

This separation is important because provider dependencies and output formats will diverge over time.

## Core Data Concepts

- `File`: the original uploaded source document
- `AnalysisRun`: one provider's run against one file
- `RawArtifact`: provider-native output
- `RenderDocument`: normalized result used by the viewer

This model makes it possible to compare many providers on one file without coupling the rest of the system to a provider-specific output shape.

## Key Challenges

- Different providers return different structures and coordinate systems.
- OCR-heavy and born-digital PDFs require different expectations.
- Provider dependencies may conflict and need isolation.
- Visual comparison is useful but can be misleading without consistent normalization.
- Large documents can create heavy overlay payloads.
- It is easy to build a demo; it is harder to build a trusted evaluation workflow.

## Risks

- If the product is positioned too broadly, it will sound like a generic "AI PDF viewer."
- If provider output is exposed directly to the frontend, the system will become hard to maintain.
- If the comparison UI is shallow, it may look like a gimmick instead of a serious evaluation tool.
- If claims about precision are made too early, credibility may suffer.

## Strategic Positioning

The strongest positioning is:

**A PDF viewer SDK and comparison interface for inspecting document analysis quality across providers.**

This is more differentiated than marketing the product as a generic viewer with AI features.

## Initial Success Criteria

- A user can upload one file and run at least two providers.
- The viewer can display the same document in multiple synchronized panes.
- Each pane can show normalized overlays for text blocks and tables.
- Users can understand differences without reading raw JSON.
- The output is strong enough to support demos, screenshots, and public technical writeups.

## Next Steps

1. Introduce an `AnalysisRun` concept in the backend.
2. Define a normalized render schema for the viewer.
3. Support multi-provider analysis on the same file.
4. Build a compare view in the frontend.
5. Add one more provider after the normalized pipeline is stable.
6. Publish comparison content using real-world documents.

## Conclusion

This is a credible and promising product direction. It creates practical value for users, forces a clean multi-provider architecture, and gives the PDF viewer SDK a sharper market identity. If executed well, it can promote both the product and the author by making the viewer the place where document analysis quality becomes visible.
