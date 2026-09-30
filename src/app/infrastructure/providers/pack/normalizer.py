"""The pack normalizer: a stored normalized document -> RenderDocument.

For in-process providers the normalizer walks the engine's raw export. For a
pack, the provider already normalized its engine's output into the contract's
Document — this side is a load plus the field-for-field mapper, with no
engine knowledge at all.
"""

from __future__ import annotations

import json

import msgspec
from docalchemy.contract import Document

from app.infrastructure.providers.pack.mapper import document_to_render_document
from app.infrastructure.render_document import RenderDocument


def pack_raw_to_render_document(
    raw_json: dict,
    provider_metadata: dict,
) -> RenderDocument:
    """`raw_json` here is the stored normalized document (artifact_type
    "normalized"), not an engine export."""
    document = msgspec.json.decode(json.dumps(raw_json).encode(), type=Document)
    return document_to_render_document(document)
