from pathlib import Path

from object_store import ObjectStore

storage_path = Path("storage")
storage = ObjectStore(storage_path.as_posix())
storage.root_path = storage_path

__all__ = [
    "storage",
]
