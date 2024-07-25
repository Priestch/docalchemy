from pathlib import Path

from object_store import ObjectStore

storage_path = Path("storage")
storage = ObjectStore(storage_path.as_posix())

__all__ = [
    "storage",
]
