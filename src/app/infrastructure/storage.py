import hashlib
import json
import os
from pathlib import Path

split_length = 2


class StorageService:
    root_path: Path

    def __init__(self, root_path: Path):
        self.root_path = root_path

    def resolve(self, name: str) -> Path:
        return self.root_path / self._get_sub_path(name)

    @staticmethod
    def _get_sub_path(name: str) -> Path:
        return Path(name[:split_length]) / name[split_length:]

    def save(self, data: dict | bytes, suffix: str = ".pdf") -> str:
        if not isinstance(data, bytes):
            data = json.dumps(data).encode()

        filename = hashlib.md5(data).hexdigest() + suffix
        file_path = self.resolve(filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(data)

        return filename

    def save_file(self, file: Path):
        with open(file, "rb") as f:
            file_hash = storage.save(f.read(), file.suffix.lower())
            print(storage.root_path, file_hash)

    def get(self, content_hash: str) -> bytes:
        with open(self.resolve(content_hash), "rb") as f:
            return f.read()


root_path = (
    Path(os.getenv("STORAGE_ROOT_PATH"))
    if os.getenv("STORAGE_ROOT_PATH")
    else Path(__file__).parent.parent.parent.parent / "storage"
)

storage = StorageService(root_path)
