"""
Soil Report Document Extractor.
Supports text-based PDF, scanned PDF, JPEG, and PNG images.
Integrates pypdf for text/image extraction, PIL for image manipulation,
local Ollama glm-ocr:latest for vision OCR, and deterministic safeguards.
"""

import io
import logging
import os
from typing import Optional, List, Tuple
from PIL import Image, ImageOps
import pypdf

from .models import (
    SoilReportExtractionResult,
    SoilReportMetadata,
    ExtractedSoilMeasurement,
    ReportExtractionStatus,
    MeasurementVerificationStatus,
    ParameterExtractionStatus,
)
from .parser import SoilReportParser
from .safeguards import ExtractionSafeguards
from .ollama_client import OllamaOCRClient

logger = logging.getLogger(__name__)

# Keywords indicating tabular soil laboratory content in digital PDFs
SOIL_TABULAR_KEYWORDS = {
    "ph", "nitrogen", "phosphorus", "potassium", "ec", "carbon", "soil",
    "sample", "lab", "laboratory", "kg/ha", "ds/m", "ppm", "mg/kg", "p2o5", "k2o",
    "zinc", "iron", "sulphur", "boron", "health card", "analysis", "test report",
}


class SoilOCRExtractor:
    """
    Multi-modal soil report extractor handling text PDFs, scanned PDFs, and JPEG/PNG images.
    """

    def __init__(
        self,
        ollama_client: Optional[OllamaOCRClient] = None,
        parser: Optional[SoilReportParser] = None,
        max_image_dimension: int = 2048,
    ):
        self.ollama_client = ollama_client or OllamaOCRClient()
        self.parser = parser or SoilReportParser()
        self.max_image_dimension = max_image_dimension

    def extract(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: Optional[str] = None,
    ) -> SoilReportExtractionResult:
        """
        Main entrypoint: detects document modality, extracts text or vision OCR,
        applies deterministic parsing and agronomic safeguards.
        """
        if not file_bytes:
            return SoilReportExtractionResult(
                document_type="unsupported",
                extraction_status=ReportExtractionStatus.FAILED.value,
                warnings=["Empty document payload provided."],
                overall_confidence=0.0,
            )

        lower_fn = filename.lower()
        is_pdf = lower_fn.endswith(".pdf") or (mime_type and "pdf" in mime_type.lower())
        is_image = (
            any(lower_fn.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"])
            or (mime_type and "image" in mime_type.lower())
        )

        try:
            if is_pdf:
                return self._process_pdf(file_bytes, filename)
            elif is_image:
                return self._process_image(file_bytes, filename, mime_type)
            else:
                return SoilReportExtractionResult(
                    document_type="unsupported",
                    extraction_status=ReportExtractionStatus.FAILED.value,
                    warnings=[f"Unsupported file format for '{filename}'. Allowed: PDF, JPEG, PNG."],
                    overall_confidence=0.0,
                )
        except Exception as exc:
            logger.exception(f"Unhandled error during document extraction for {filename}: {exc}")
            return SoilReportExtractionResult(
                document_type="unsupported",
                extraction_status=ReportExtractionStatus.FAILED.value,
                warnings=[f"Extraction failed due to internal error: {str(exc)}"],
                overall_confidence=0.0,
            )

    def _process_pdf(self, file_bytes: bytes, filename: str) -> SoilReportExtractionResult:
        """
        Distinguishes between text-based PDF and scanned PDF.
        Extracts native text stream or embedded raster images for OCR.
        """
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        num_pages = len(reader.pages)
        if num_pages == 0:
            return SoilReportExtractionResult(
                document_type="text_pdf",
                extraction_status=ReportExtractionStatus.FAILED.value,
                warnings=["PDF file contains zero pages."],
                overall_confidence=0.0,
            )

        # 1. Extract digital text streams
        extracted_pages = []
        for p in reader.pages:
            try:
                extracted_pages.append(p.extract_text() or "")
            except Exception:
                extracted_pages.append("")
        full_text = "\n".join(extracted_pages).strip()

        # Check if text is sufficient and contains soil keywords
        text_lower = full_text.lower()
        has_soil_keywords = any(kw in text_lower for kw in SOIL_TABULAR_KEYWORDS)

        if len(full_text) >= 100 and has_soil_keywords:
            logger.info(f"Processing '{filename}' as text-based PDF ({len(full_text)} chars).")
            metadata, measurements = self.parser.parse(full_text, pages=extracted_pages)
            result = SoilReportExtractionResult(
                document_type="text_pdf",
                extraction_status=ReportExtractionStatus.EXTRACTION_COMPLETED.value,
                metadata=metadata,
                measurements=measurements,
                raw_text=full_text,
                overall_confidence=1.0,
            )
            return ExtractionSafeguards.apply(result)

        # 2. Text was insufficient or missing — Treat as Scanned PDF
        logger.info(f"Processing '{filename}' as scanned PDF (extracting page raster images).")
        page_images: List[Image.Image] = []
        for page_idx, page in enumerate(reader.pages):
            page_imgs = []
            for img_obj in page.images:
                try:
                    img_data = img_obj.data
                    pil_img = Image.open(io.BytesIO(img_data))
                    page_imgs.append(pil_img)
                except Exception as e:
                    logger.warning(f"Failed to decode embedded image on page {page_idx}: {e}")
            if page_imgs:
                # If multiple tiles exist per page, stitch vertically
                stitched = self._stitch_images(page_imgs)
                page_images.append(stitched)

        if not page_images:
            # Fall back to whatever text was available
            if full_text:
                metadata, measurements = self.parser.parse(full_text, pages=extracted_pages)
                result = SoilReportExtractionResult(
                    document_type="text_pdf",
                    extraction_status=ReportExtractionStatus.EXTRACTION_COMPLETED.value,
                    metadata=metadata,
                    measurements=measurements,
                    raw_text=full_text,
                    overall_confidence=0.70,
                )
                return ExtractionSafeguards.apply(result)

            return SoilReportExtractionResult(
                document_type="scanned_pdf",
                extraction_status=ReportExtractionStatus.FAILED.value,
                warnings=["Scanned PDF contains no readable text streams or embedded page images."],
                overall_confidence=0.0,
            )

        # Transcribe extracted images via Ollama OCR
        ocr_texts = []
        for idx, p_img in enumerate(page_images):
            prep_bytes = self._prepare_image_bytes(p_img)
            ocr_content = self.ollama_client.transcribe_image(prep_bytes, mime_type="image/png")
            ocr_texts.append(ocr_content)

        composite_ocr_text = "\n\n".join(ocr_texts)
        metadata, measurements = self.parser.parse(composite_ocr_text, pages=ocr_texts)

        result = SoilReportExtractionResult(
            document_type="scanned_pdf",
            extraction_status=ReportExtractionStatus.EXTRACTION_COMPLETED.value,
            metadata=metadata,
            measurements=measurements,
            raw_text=composite_ocr_text,
            overall_confidence=0.88,
        )
        return ExtractionSafeguards.apply(result)

    def _process_image(
        self, file_bytes: bytes, filename: str, mime_type: Optional[str]
    ) -> SoilReportExtractionResult:
        """
        Decodes JPEG/PNG image, corrects orientation, downscales if necessary,
        and executes OCR transcription.
        """
        doc_type = "image_png" if filename.lower().endswith(".png") else "image_jpeg"

        try:
            pil_img = Image.open(io.BytesIO(file_bytes))
        except Exception as e:
            return SoilReportExtractionResult(
                document_type=doc_type,
                extraction_status=ReportExtractionStatus.FAILED.value,
                warnings=[f"Failed to decode image data: {e}"],
                overall_confidence=0.0,
            )

        # Transcribe with Ollama
        prep_bytes = self._prepare_image_bytes(pil_img)
        ocr_text = self.ollama_client.transcribe_image(
            prep_bytes, mime_type="image/jpeg" if doc_type == "image_jpeg" else "image/png"
        )

        metadata, measurements = self.parser.parse(ocr_text)

        result = SoilReportExtractionResult(
            document_type=doc_type,
            extraction_status=ReportExtractionStatus.EXTRACTION_COMPLETED.value,
            metadata=metadata,
            measurements=measurements,
            raw_text=ocr_text,
            overall_confidence=0.90,
        )
        return ExtractionSafeguards.apply(result)

    def _prepare_image_bytes(self, img: Image.Image) -> bytes:
        """
        Validates EXIF orientation, converts color mode to RGB,
        and resizes to max dimension while preserving aspect ratio.
        """
        # 1. Correct EXIF rotation
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # 2. Convert to RGB
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # 3. Downscale if dimensions exceed max_image_dimension
        w, h = img.size
        max_dim = max(w, h)
        if max_dim > self.max_image_dimension:
            scale = self.max_image_dimension / float(max_dim)
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # 4. Save to bytes
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92)
        return buf.getvalue()

    def _stitch_images(self, images: List[Image.Image]) -> Image.Image:
        """
        Stitches multiple vertical image tiles into a single coherent image.
        """
        if len(images) == 1:
            return images[0]

        max_width = max(im.width for im in images)
        total_height = sum(im.height for im in images)

        stitched = Image.new("RGB", (max_width, total_height), color=(255, 255, 255))
        y_offset = 0
        for im in images:
            if im.mode != "RGB":
                im = im.convert("RGB")
            stitched.paste(im, (0, y_offset))
            y_offset += im.height

        return stitched


# Alias for cross-module integration
DocumentExtractionPipeline = SoilOCRExtractor
