"""Provider infrastructure: PackAdapter for all external providers.

All providers run as separate processes accessed via docalchemy.host.
The old in-process adapters have been removed in favor of the pack architecture.
"""

from app.infrastructure.providers.pack import PackAdapter

__all__ = ["PackAdapter"]
