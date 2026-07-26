from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.domain.providers.contract import (
    ProviderAdapter,
    ProviderCapabilities,
    ProviderError,
    ProviderInput,
    ProviderOutput,
    RawArtifact,
)
from app.infrastructure.storage import StorageService

# focr is a CPU-only Rust binary (not pip-installable); it ships in the image
# and the ~3.9 GB unlimited-ocr model lives in the shared cache mount.
DEFAULT_BINARY = os.getenv("FOCR_BINARY", "focr")
DEFAULT_DPI = 150
# focr does ~50 s/page on CPU plus a one-shot model load; scale the subprocess
# timeout with page count so big PDFs aren't killed prematurely.
SECONDS_PER_PAGE = 120
BASE_TIMEOUT_SECONDS = 300


class FrankenOcrAdapter(ProviderAdapter):
    def __init__(self, storage: StorageService) -> None:
        self._storage = storage

    @property
    def provider_id(self) -> str:
        return "franken_ocr"

    @property
    def provider_version(self) -> str:
        return "0.3"

    @property
    def supported_mime_types(self) -> list[str]:
        return ["application/pdf"]

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            has_ocr=True,
            has_table_extraction=True,
            has_reading_order=True,
            has_formula=True,
            has_image_description=False,
        )

    def execute(self, input: ProviderInput) -> ProviderOutput:
        source_path = self._storage.resolve(input.source_storage_key)
        config = input.config or {}
        dpi = int(config.get("dpi", DEFAULT_DPI))
        binary = config.get("focr_binary") or DEFAULT_BINARY

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            page_images = self._rasterize(source_path, tmp, dpi)
            if not page_images:
                raise ProviderError(
                    error_code="FOCR_NO_PAGES",
                    error_message=f"PDF rendered 0 pages: {source_path}",
                )

            # focr's native PDF fast path only accepts image PDFs, and `ocr-batch`
            # drops layout geometry. So rasterize → reassemble as an image-only
            # PDF → one `focr ocr` invocation: the model loads ONCE and we get
            # per-page region boxes for the whole document.
            image_pdf = tmp / "doc.pdf"
            self._build_image_pdf([img[0] for img in page_images], image_pdf)
            raw = self._run_focr(binary, image_pdf, tmp / "out.json", len(page_images))

        # Stamp each page with both the rasterized pixel dims (focr emits region
        # boxes in raster pixel space) and the PDF page size in points. The
        # normalizer normalizes boxes by pixels → [0,1], and reports the page in
        # points, which is the unit the PDF viewer's annotation layer expects.
        pages = raw.get("pages", [])
        for i, page in enumerate(pages):
            page.setdefault("page_index", i)
            if i < len(page_images):
                _, px_w, px_h, pt_w, pt_h = page_images[i]
                page["pixel_width"] = px_w
                page["pixel_height"] = px_h
                page["page_width"] = pt_w
                page["page_height"] = pt_h

        storage_key = self._storage.save(raw, suffix=".json")

        region_count = sum(len(p.get("layout", [])) for p in pages)
        return ProviderOutput(
            raw_artifacts=[
                RawArtifact(
                    artifact_type="raw_json",
                    storage_key=storage_key,
                    format="json",
                )
            ],
            metadata={
                "pages_processed": len(pages),
                "layout_regions": region_count,
                "has_markdown": bool(raw.get("markdown")),
            },
        )

    @staticmethod
    def _rasterize(pdf_path: Path, out_dir: Path, dpi: int) -> list[tuple[Path, int, int, float, float]]:
        import pypdfium2 as pdfium  # heavy import, defer to call site

        document = pdfium.PdfDocument(str(pdf_path))
        scale = dpi / 72.0
        images: list[tuple[Path, int, int, float, float]] = []
        for index, page in enumerate(document):
            pt_w, pt_h = page.get_size()  # PDF points (the unit the viewer expects)
            pil_image = page.render(scale=scale).to_pil()
            out_path = out_dir / f"page_{index + 1:04d}.png"
            pil_image.save(out_path)
            images.append((out_path, pil_image.width, pil_image.height, float(pt_w), float(pt_h)))
        return images

    @staticmethod
    def _build_image_pdf(image_paths: list[Path], out_pdf: Path) -> None:
        from PIL import Image  # heavy import, defer to call site

        pages = [Image.open(p).convert("RGB") for p in image_paths]
        pages[0].save(out_pdf, save_all=True, append_images=pages[1:])

    @staticmethod
    def _run_focr(binary: str, image_pdf: Path, out_json: Path, page_count: int) -> dict:
        if not shutil.which(binary):
            raise ProviderError(
                error_code="FOCR_CLI_MISSING",
                error_message=(
                    f"focr CLI not found at {binary!r}. The franken_ocr image must "
                    "install the focr binary and the model under FOCR_MODEL_DIR."
                ),
            )

        cmd = [binary, "ocr", str(image_pdf), "-o", str(out_json)]
        timeout = BASE_TIMEOUT_SECONDS + SECONDS_PER_PAGE * max(1, page_count)
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        if completed.returncode != 0:
            detail = (completed.stdout or "") + (completed.stderr or "")
            raise ProviderError(
                error_code="FOCR_CLI_ERROR",
                error_message=f"focr ocr exited {completed.returncode}: {detail[-2000:]}",
            )

        try:
            return json.loads(out_json.read_text())
        except (json.JSONDecodeError, FileNotFoundError) as exc:
            raise ProviderError(
                error_code="FOCR_BAD_OUTPUT",
                error_message=f"focr ocr produced no parseable JSON ({exc})",
            ) from exc
