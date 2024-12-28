import logging
import os
from pathlib import Path

from docling.document_converter import DocumentConverter

from app.infrastructure.storage import storage

os.environ["HF_HOME"] = str(Path(__file__).parent.parent / "storage" / "huggingface")

if __name__ == "__main__":
    logger = logging.getLogger("docling")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    converter = DocumentConverter()
    # pdf_path = Path(__file__).parent / "2408.09869v5.pdf"
    pdf_path = Path(storage.resolve("361943fe584e2f3332f7bc9e056b11d0.pdf"))

    result = converter.convert(pdf_path, max_file_size=20971520)
    doc = result.document.export_to_dict()
    file_hash = storage.save(doc, suffix=".json")
    # print(file_hash)
    # with open(pdf_path, "rb") as f:
    #     file_hash = storage.save(f.read())
    #     print(storage.root_path, file_hash)
    # with open("output.json", "w") as f:
    #     json.dump(doc, f, indent=4)
