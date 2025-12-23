"""DeepSeek OCR engine adapter.

Uses the deepseek-ocr-cli tool for local OCR processing via Ollama.
CLI: https://github.com/r-uben/deepseek-ocr-cli
"""

import json
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image

from docr.core.config import DeepSeekConfig
from docr.core.result import FigureResult, PageResult
from docr.engines.base import BaseEngine, EngineCapabilities


class DeepSeekEngine(BaseEngine):
    """Adapter for DeepSeek OCR via CLI tool.

    Uses the deepseek-ocr-cli which wraps DeepSeek-OCR running on Ollama.
    """

    def __init__(self, config: DeepSeekConfig | None = None) -> None:
        super().__init__()
        self.config = config or DeepSeekConfig()

    @property
    def name(self) -> str:
        return "deepseek"

    @property
    def capabilities(self) -> EngineCapabilities:
        return EngineCapabilities(
            name="deepseek",
            supports_pdf=False,  # Process via images
            supports_images=True,
            supports_batch=False,
            supports_figures=True,  # Can describe figures
            is_local=True,
            cost_per_page=0.0,
            best_for=["general", "multilingual", "tables"],
        )

    def initialize(self) -> bool:
        """Check if deepseek-ocr CLI is available."""
        if self._initialized:
            return True

        try:
            # Check if CLI is installed
            result = subprocess.run(
                ["deepseek-ocr", "info"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self._initialized = result.returncode == 0
            return self._initialized
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def process_image(self, image: Image.Image, page_num: int = 1) -> PageResult:
        """Process a single image with DeepSeek CLI."""
        if not self._initialized and not self.initialize():
            return self._create_error_result(page_num, "DeepSeek CLI not installed")

        start_time = time.time()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Save image
            image_file = tmp_path / "input.png"
            image.save(image_file, format="PNG")

            # Run CLI
            try:
                cmd = [
                    "deepseek-ocr",
                    str(image_file),
                    "-o", str(tmp_path),
                    "--model", self.config.model,
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.config.timeout,
                )

                if result.returncode != 0:
                    return self._create_error_result(
                        page_num,
                        f"DeepSeek CLI failed: {result.stderr}"
                    )

                # Read output markdown
                output_file = tmp_path / "input.md"
                if not output_file.exists():
                    return self._create_error_result(
                        page_num,
                        "DeepSeek CLI did not generate output file"
                    )

                text = output_file.read_text()

                # Remove metadata frontmatter if present
                if text.startswith("---"):
                    parts = text.split("---", 2)
                    if len(parts) >= 3:
                        text = parts[2].strip()

                processing_time = time.time() - start_time

                return self._create_success_result(
                    page_num=page_num,
                    text=text,
                    processing_time=processing_time,
                )

            except subprocess.TimeoutExpired:
                return self._create_error_result(
                    page_num,
                    f"DeepSeek CLI timeout after {self.config.timeout}s"
                )
            except Exception as e:
                return self._create_error_result(page_num, str(e))

    def describe_figure(
        self,
        image: Image.Image,
        figure_type: str = "unknown",
        context: str = "",
    ) -> FigureResult:
        """Describe a figure using DeepSeek vision via CLI."""
        if not self._initialized and not self.initialize():
            return FigureResult(
                figure_num=0,
                page_num=0,
                figure_type=figure_type,
                description="DeepSeek CLI not installed",
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Save image
            image_file = tmp_path / "figure.png"
            image.save(image_file, format="PNG")

            # Build prompt
            prompt = "Describe this figure in detail. What does the chart/graph/diagram show? Explain the axes, data, and key findings."
            if context:
                prompt += f"\n\nContext from surrounding text: {context}"

            try:
                cmd = [
                    "deepseek-ocr",
                    str(image_file),
                    "-o", str(tmp_path),
                    "--prompt", prompt,
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode != 0:
                    return FigureResult(
                        figure_num=0,
                        page_num=0,
                        figure_type=figure_type,
                        description=f"Error: {result.stderr}",
                    )

                # Read output
                output_file = tmp_path / "figure.md"
                if output_file.exists():
                    description = output_file.read_text().strip()

                    # Remove metadata if present
                    if description.startswith("---"):
                        parts = description.split("---", 2)
                        if len(parts) >= 3:
                            description = parts[2].strip()
                else:
                    description = "No description generated"

                # Try to extract figure type from response
                detected_type = figure_type
                for t in ["chart", "graph", "table", "diagram", "photo", "image"]:
                    if t in description.lower():
                        detected_type = t
                        break

                return FigureResult(
                    figure_num=0,
                    page_num=0,
                    figure_type=detected_type,
                    description=description,
                    engine=self.name,
                )

            except Exception as e:
                return FigureResult(
                    figure_num=0,
                    page_num=0,
                    figure_type=figure_type,
                    description=f"Error: {e}",
                )
