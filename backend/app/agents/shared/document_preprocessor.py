"""
Stage 0: Document Preprocessor.

Pipeline:
  Digital PDF → MinerU (if installed) → Markdown + tables + chapter hints
  Scanned PDF → PaddleOCR (if installed) → text → MinerU path
  Fallback   → pypdf + python-docx (always available)
"""

import logging
import re
from io import BytesIO
from pathlib import Path
from typing import Any

from docx import Document
from pypdf import PdfReader

logger = logging.getLogger(__name__)

try:
    import magic_pdf  # MinerU's Python package

    HAS_MINERU = True
except ImportError:
    HAS_MINERU = False
    logger.info("MinerU not installed — falling back to pypdf for PDF extraction")

try:
    import tabula

    HAS_TABULA = True
except ImportError:
    HAS_TABULA = False
    logger.info("tabula-py not installed — PDF table extraction unavailable in pypdf fallback")

try:
    from paddleocr import PaddleOCR

    HAS_PADDLEOCR = True
except ImportError:
    HAS_PADDLEOCR = False
    logger.info("PaddleOCR not installed — scanned PDF OCR unavailable")


class DocumentPreprocessor:
    """Parse a contract file into clean Markdown text + structured tables."""

    def __init__(self, use_ocr: bool = False):
        self.use_ocr = use_ocr
        self._ocr = None

    def parse(self, uploaded_file) -> dict[str, Any]:
        """
        Parse an uploaded file into structured output.

        Args:
            uploaded_file: Streamlit UploadedFile or a file path string

        Returns:
            {
                "markdown": str,          # full document in clean markdown
                "tables": List[Dict],      # extracted tables as list of dicts
                "page_count": int,         # total pages (PDF only)
                "format": str,             # "digital_pdf" | "scanned_pdf" | "docx" | "text"
                "parser_used": str,        # "mineru" | "pypdf" | "python-docx" | "native"
                "raw_text": str,           # plain text fallback
            }
        """
        name = getattr(uploaded_file, "name", str(uploaded_file))
        data = getattr(uploaded_file, "read", lambda: None)()
        if data is None and isinstance(uploaded_file, (str, Path)):
            with open(uploaded_file, "rb") as f:
                data = f.read()

        ext = Path(name).suffix.lower()

        if ext == ".pdf":
            return self._parse_pdf(BytesIO(data), name)
        elif ext in (".docx", ".doc"):
            return self._parse_docx(BytesIO(data))
        elif ext in (".txt", ".md", ".markdown"):
            return self._parse_text(data.decode("utf-8", errors="ignore"))
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _parse_pdf(self, stream: BytesIO, name: str) -> dict[str, Any]:
        if HAS_MINERU:
            try:
                return self._parse_pdf_mineru(stream)
            except Exception as e:
                logger.warning("MinerU parse failed (%s), falling back to pypdf", e)

        return self._parse_pdf_pypdf(stream)

    def _parse_pdf_mineru(self, stream: BytesIO) -> dict[str, Any]:
        """Parse PDF using MinerU for high-fidelity extraction."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(stream.getvalue())
            tmp_path = tmp.name

        try:
            result = magic_pdf.parse_pdf(tmp_path)
            markdown = result.get("markdown", "")
            tables = result.get("tables", [])
            raw_text = result.get("text", "")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        return self._build_output(markdown or raw_text, tables, "digital_pdf", "mineru")

    def _parse_pdf_pypdf(self, stream: BytesIO) -> dict[str, Any]:
        """Fallback PDF parser using pypdf."""
        reader = PdfReader(stream)
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)

        full_text = "\n".join(pages)
        is_scanned = self._detect_scanned(full_text)

        if is_scanned and self.use_ocr and HAS_PADDLEOCR:
            full_text = self._ocr_pdf(reader)

        fmt = "scanned_pdf" if is_scanned else "digital_pdf"
        tables = self._extract_tables_tabula(stream) if HAS_TABULA else []
        return self._build_output(full_text, tables, fmt, "pypdf")

    def _extract_tables_tabula(self, stream: BytesIO) -> list[list[list[str]]]:
        """Extract tables from PDF using tabula-py."""
        import tempfile

        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(stream.getvalue())
                tmp_path = tmp.name

            try:
                dfs = tabula.read_pdf(tmp_path, pages="all", silent=True)
                tables = []
                for df in dfs:
                    if not df.empty:
                        rows = [df.columns.tolist(), *df.values.tolist()]
                        tables.append([[str(cell) for cell in row] for row in rows])
                return tables
            finally:
                Path(tmp_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning("tabula table extraction failed: %s", e)
            return []

    def _detect_scanned(self, text: str) -> bool:
        """Heuristic: if extracted text is nearly empty, the PDF is likely scanned."""
        meaningful = re.sub(r"\s+", "", text)
        return len(meaningful) < 100

    def _ocr_pdf(self, reader: PdfReader) -> str:
        """Run PaddleOCR on each page of a scanned PDF."""
        if self._ocr is None:
            self._ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        pages = []
        for page in reader.pages:
            image = page.images[0] if page.images else None
            if image is None:
                pages.append("")
                continue
            result = self._ocr.ocr(image.data, cls=True)
            text = " ".join([line[1][0] for line in result[0]]) if result and result[0] else ""
            pages.append(text)
        return "\n".join(pages)

    def _parse_docx(self, stream: BytesIO) -> dict[str, Any]:
        doc = Document(stream)
        paragraphs = []
        tables = []

        for element in doc.element.body:
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
            if tag == "p":
                text = element.text or ""
                paragraphs.append(text)
            elif tag == "tbl":
                table_data = self._extract_docx_table(element, doc)
                if table_data:
                    tables.append(table_data)

        full_text = "\n".join(p for p in paragraphs if p.strip())
        return self._build_output(full_text, tables, "docx", "python-docx")

    def _extract_docx_table(self, tbl_element, doc) -> list[list[str]] | None:
        """Extract a single DOCX table into a list of rows."""
        rows = []
        for row in tbl_element.findall(
            ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr"
        ):
            cells = []
            for cell in row.findall(
                ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc"
            ):
                text = "".join(cell.itertext()).strip()
                cells.append(text)
            if any(cells):
                rows.append(cells)
        return rows if rows else None

    def _parse_text(self, text: str) -> dict[str, Any]:
        return self._build_output(text, [], "text", "native")

    def _build_output(self, text: str, tables: list[Any], fmt: str, parser: str) -> dict[str, Any]:
        markdown = self._text_to_markdown(text)
        page_count = self._estimate_pages(text)
        return {
            "markdown": markdown,
            "tables": tables,
            "page_count": page_count,
            "format": fmt,
            "parser_used": parser,
            "raw_text": text,
        }

    @staticmethod
    def _text_to_markdown(text: str) -> str:
        """Normalise extracted text into clean Markdown."""
        lines = text.split("\n")
        cleaned = []
        prev_empty = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if not prev_empty:
                    cleaned.append("")
                prev_empty = True
            else:
                cleaned.append(stripped)
                prev_empty = False

        # Remove leading/trailing blank lines
        while cleaned and not cleaned[0]:
            cleaned.pop(0)
        while cleaned and not cleaned[-1]:
            cleaned.pop()

        return "\n".join(cleaned)

    @staticmethod
    def _estimate_pages(text: str) -> int:
        chinese_chars = sum(1 for ch in text if "一" <= ch <= "鿿")
        if chinese_chars > 0:
            return max(1, chinese_chars // 500)
        return max(1, len(text) // 2500)
