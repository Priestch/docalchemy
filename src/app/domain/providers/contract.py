from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ProviderCapabilities:
    has_ocr: bool = False
    has_table_extraction: bool = False
    has_reading_order: bool = False
    has_formula: bool = False
    has_image_description: bool = False


@dataclass
class ProviderInput:
    source_storage_key: str
    source_mime_type: str
    config: dict = field(default_factory=dict)


@dataclass
class RawArtifact:
    artifact_type: str  # "raw_json" | "raw_markdown" | "raw_html"
    storage_key: str
    format: str  # "json" | "md" | "html"


@dataclass
class ProviderOutput:
    raw_artifacts: list[RawArtifact] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class ProviderError(Exception):
    def __init__(self, error_code: str, error_message: str, recoverable: bool = False) -> None:
        self.error_code = error_code
        self.error_message = error_message
        self.recoverable = recoverable
        super().__init__(error_message)


class ProviderAdapter(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str: ...

    @property
    @abstractmethod
    def provider_version(self) -> str: ...

    @property
    @abstractmethod
    def supported_mime_types(self) -> list[str]: ...

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities: ...

    @abstractmethod
    def execute(self, input: ProviderInput) -> ProviderOutput: ...
