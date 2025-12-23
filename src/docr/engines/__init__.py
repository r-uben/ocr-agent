"""OCR engine adapters."""

from docr.engines.base import BaseEngine, EngineCapabilities
from docr.engines.deepseek import DeepSeekEngine
from docr.engines.gemini import GeminiEngine
from docr.engines.mistral import MistralEngine
from docr.engines.nougat import NougatEngine

__all__ = [
    "BaseEngine",
    "EngineCapabilities",
    "NougatEngine",
    "DeepSeekEngine",
    "MistralEngine",
    "GeminiEngine",
]
