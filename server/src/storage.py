from pathlib import Path

pdf_dir = "pdf"
json_dir = "json"


class Storage:
    def __init__(self, path):
        self.path = path

    @property
    def pdf_dir(self):
        return self.path / pdf_dir

    def get_path(self, filename):
        return self.path / pdf_dir / filename

    def get_json_path(self, filename):
        return self.path / json_dir / filename

    def ensure_path(self):
        pass


# TODO: make this configurable
storage_path = Path('/home/gaopeng/Enter/docalchemy/storage')
storage = Storage(storage_path)
