from pathlib import Path
from typing import Self

from docling.document_converter import DocumentConverter

from analyser.storage_service import storage


class Analyser:
    converter: DocumentConverter

    def __init__(self, converter: DocumentConverter):
        self.converter = converter

    @classmethod
    def configure(cls) -> Self:
        converter = DocumentConverter()
        return cls(converter)

    def analyse(self, source: Path) -> None:
        result = self.converter.convert(source)
        doc = result.document.export_to_dict()
        file_hash = storage.save(doc, suffix=".json")
        print("DoclingAnalyser", "analyse", source, file_hash)
