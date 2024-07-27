from typing import TYPE_CHECKING

from .analyzer import Analyzer

if TYPE_CHECKING:
    from object_store import ObjectStore
    from pathlib import Path


class FurnaceService:
    def __init__(self, storage: "ObjectStore"):
        self.storage = storage
        self.analyzer = Analyzer()

    def with_analyzer(self, analyzer: Analyzer):
        self.analyzer = analyzer

        return self

    def start(self, file_path: "Path"):
        self.analyzer.analyze(file_path)


