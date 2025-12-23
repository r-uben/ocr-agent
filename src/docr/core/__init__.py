"""Core data models for docr."""

from docr.core.config import AgentConfig
from docr.core.document import Document, PageImage
from docr.core.result import OCRResult, PageResult, ProcessingStats

__all__ = [
    "AgentConfig",
    "Document",
    "PageImage",
    "OCRResult",
    "PageResult",
    "ProcessingStats",
]
