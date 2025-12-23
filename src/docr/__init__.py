"""docr - Multi-agent document processing with beautiful terminal UI."""

__version__ = "0.1.0"

from docr.core.config import AgentConfig
from docr.core.document import Document, DocumentType
from docr.core.result import OCRResult, PageResult
from docr.pipeline.processor import OCRPipeline

__all__ = [
    "AgentConfig",
    "Document",
    "DocumentType",
    "OCRResult",
    "PageResult",
    "OCRPipeline",
]
