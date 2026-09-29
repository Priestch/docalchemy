"""Adapter-side mapping: the DocAlchemy contract Document -> RenderDocument.

The contract's Document is what a provider pack returns over the job
protocol; RenderDocument is this service's frontend contract (ADR 0004).
This mapper is the view layer between them — a field-for-field translation
with no extraction logic: everything positional, tabular, or textual was
already normalized inside the provider.
"""
