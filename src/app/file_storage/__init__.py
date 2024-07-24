import os
from pathlib import Path

from object_store import ObjectStore


storage_path = "storage"
# work_dir = os.getcwd()
# if work_dir.endswith("src/app"):
#     storage_path = (Path(work_dir).parent.parent / storage_path).as_posix()
storage = ObjectStore(storage_path)

__all__ = [
    "storage"
]
