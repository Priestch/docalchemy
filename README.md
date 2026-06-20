# DocAlchemy

> One document in. Every analysis engine's understanding of it, normalized and inspectable in one place.

## Why does this exist?

Document analysis is hard to trust. Today, anyone who needs to understand what a
document *actually contains* — an engineering team picking an OCR engine, a data
team building an ingestion pipeline, a researcher comparing extraction quality —
is forced to work across a landscape of providers that **do not speak the same
language**.

Each engine (Docling, OpenDataLoader, and many others) ships its own output
format, its own coordinate system, its own notion of a "block," a "table," a
"reading order." Evaluating even a single provider means staring at raw JSON,
writing throwaway scripts, and eyeballing screenshots. Comparing two providers
on the same file means doing all of that twice and holding the results in your
head. The real question — *which engine actually understands this document?* —
never gets a clean answer.

### Benchmarks lie

So how do people decide today? They read benchmark reports. And benchmarks lie.

Not always deliberately, but reliably. Vendor benchmarks are run on curated
datasets chosen to flatter the seller, in tuned configurations you'll never
reproduce, against tasks that may have nothing to do with yours. A table that
scores 98% on the benchmark merges two columns on page 4 of *your* invoice. An
engine that "leads the field" drops the reading order on the document layout
your team actually ships. Aggregate accuracy over a dataset you don't have is a
marketing number, not a decision. By the time it has been averaged, weighted,
and put on a leaderboard, it no longer describes any single real document —
including yours.

The only benchmark that matters is the one run on the document in front of you,
seen with your own eyes. DocAlchemy exists to make that benchmark possible.

### What replaces the leaderboard

The core idea is a **provider-neutral inspection layer for document
analysis**. Upload a source document once. Run it through as many analysis
engines as you like. DocAlchemy stores each engine's raw output, normalizes
every one of them into a single stable schema, and renders the results as
overlays on top of the **original** document — so the source PDF is always the
visual ground truth, and every provider is judged against the same baseline.

This matters because layout and structure quality is *qualitative first*. You
can read a hundred benchmark metrics about table extraction and still not know
whether an engine merged two columns on page 4. You can see it in a second when
the engine's extracted table is drawn over the real one. DocAlchemy turns
"trust the extraction" from a leap of faith into something you can look at.

In short: the document-analysis industry has no neutral ground for seeing what
its engines actually do — only leaderboards that flatten the truth away.
DocAlchemy builds that ground: one stable render contract, every provider
isolated and replaceable, the source document always at the center, and your
own eyes as the judge.

## What it does

- **Ingest once.** Upload a single source document; it is stored as the
  immutable visual baseline for every analysis.
- **Run many engines.** Dispatch the same source through multiple analysis
  providers (Docling and OpenDataLoader today; more behind a stable contract).
- **Normalize to one schema.** Each provider's native output is converted into
  an app-owned `RenderDocument` schema — one coordinate system, one block model,
  one way to render. The frontend never sees provider-native JSON.
- **Inspect over the real document.** Render normalized blocks, tables,
  reading order, and figures as overlays on the original PDF, so quality is
  judged visually against the source — not against a leaderboard. The viewer is
  powered by [document-viewer](https://github.com/Priestch/document-viewer),
  an open-source PDF viewing SDK maintained by the same author.
- **Track every run.** Provider name, version, config, latency, and raw
  artifacts are recorded for every analysis, so results are reproducible.

## How it's organized

DocAlchemy is a pragmatically-DDD Python backend (Litestar) plus a React/Vite
viewer, with provider runtimes isolated behind a single contract.

- **Ingestion** — file upload and source storage.
- **Orchestration** — provider selection, job dispatch (Celery), retries, and
  run-status tracking.
- **Provider runtimes** — each engine runs in its own isolated environment with
  its own dependencies, behind the provider contract.
- **Normalization & rendering** — converts provider output into the
  `RenderDocument` schema and serves it to the viewer.

The one rule that keeps this coherent: **the application owns a single stable
render schema.** Providers come and go; the schema — and the viewer built on
it — stays.

## Documentation

Detailed design lives in [`docs/`](docs/):

- [Architecture handoff](docs/ARCHITECTURE_HANDOFF.md)
- [RenderDocument schema](docs/specs/RENDER_DOCUMENT_SCHEMA.md)
- [Provider contract](docs/specs/PROVIDER_CONTRACT.md)

## Powered by document-viewer

The inspection experience — rendering the source PDF and drawing normalized
provider overlays on top of it — is built on
[**document-viewer**](https://github.com/Priestch/document-viewer), an
open-source PDF viewing SDK maintained by the same author. DocAlchemy is both a
user of that SDK and a showcase for what a viewer becomes when it's treated as
an *inspection tool* for document intelligence rather than just a renderer.

## Status

Early. Multi-provider ingestion, normalization, and viewer overlays work; this
is not yet a released product. Expect breaking changes until a first tag.
