from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pdfplumber
from pypdf import PdfReader, PdfWriter

from paccaassure_common_tools.adapters.common import (
    finalize_result,
    library_versions,
    resolve_input_file,
    rows_to_canonical_table,
)
from paccaassure_common_tools.artifacts import ArtifactCollector
from paccaassure_common_tools.exceptions import InputValidationError
from paccaassure_common_tools.interfaces import ToolAdapter
from paccaassure_common_tools.models import (
    CanonicalDocumentOutput,
    CanonicalTableOutput,
    CertificationVerdict,
    NetworkPolicy,
    StagedArtifact,
    ToolCapability,
    ToolEvidence,
    ToolIdentity,
    ToolMaturity,
    ToolMetrics,
    ToolRegistration,
)


def _reader(path: Path) -> PdfReader:
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            raise InputValidationError(
                "Encrypted PDF requires credentials.", details={"file_name": path.name}
            )
        return reader
    except InputValidationError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise InputValidationError(
            "The PDF could not be opened.",
            details={"file_name": path.name, "exception_type": type(exc).__name__},
        ) from exc


def _classify_pdf(path: Path) -> str:
    with pdfplumber.open(str(path)) as pdf:
        text_pages = 0
        image_pages = 0
        for page in pdf.pages:
            text = (page.extract_text() or "").strip()
            if text:
                text_pages += 1
            else:
                image_pages += 1
        if text_pages and image_pages:
            return "mixed"
        if image_pages and not text_pages:
            return "ocr_required"
        return "text_based"


def _pages_list(value: object) -> list[int]:
    if not isinstance(value, list):
        return []
    pages: list[int] = []
    for item in value:
        if isinstance(item, int):
            pages.append(item)
        elif isinstance(item, str) and item.isdigit():
            pages.append(int(item))
    return pages


def _optional_int(value: object, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return default


class PdfInspectTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        path = resolve_input_file(payload, context)
        reader = _reader(path)
        classification = _classify_pdf(path)
        outputs = {
            "metadata": {key: str(value) for key, value in (reader.metadata or {}).items()},
            "page_count": len(reader.pages),
            "encrypted": reader.is_encrypted,
            "scanned_status": classification,
        }
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="pdf_inspect",
                details=outputs,
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("pypdf", "pdfplumber"),
            outputs=outputs,
            warnings=[],
            evidence=evidence,
            metrics=ToolMetrics(
                pages=len(reader.pages),
                adapter_library_versions=library_versions("pypdf", "pdfplumber"),
            ),
        )


class PdfReadTextTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        path = resolve_input_file(payload, context)
        classification = _classify_pdf(path)
        if classification == "ocr_required":
            raise InputValidationError(
                "PDF is image-based and requires OCR.", details={"file_name": path.name}
            )
        pages = []
        with pdfplumber.open(str(path)) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                pages.append({"page_number": index, "text": page.extract_text() or ""})
        output = CanonicalDocumentOutput(
            document={
                "metadata": {"file_name": path.name},
                "pages": pages,
                "sections": [],
                "tables": [],
                "links": [],
                "images": [],
            },
            metrics={"page_count": len(pages)},
            provenance={"classification": classification},
        )
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="pdf_read_text",
                details={"page_count": len(pages)},
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("pdfplumber"),
            outputs={"document_output": output.model_dump(mode="json")},
            warnings=[],
            evidence=evidence,
            metrics=ToolMetrics(
                pages=len(pages), adapter_library_versions=library_versions("pdfplumber")
            ),
        )


class PdfReadTablesTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        path = resolve_input_file(payload, context)
        tables = []
        with pdfplumber.open(str(path)) as pdf:
            for page_index, page in enumerate(pdf.pages, start=1):
                extracted = page.extract_tables()
                for table_index, table in enumerate(extracted, start=1):
                    if not table or not table[0]:
                        continue
                    headers = [cell or f"column_{i+1}" for i, cell in enumerate(table[0])]
                    rows = table[1:]
                    tables.append(
                        rows_to_canonical_table(
                            name=f"page_{page_index}_table_{table_index}",
                            source={
                                "type": "pdf",
                                "file_name": path.name,
                                "page_number": page_index,
                            },
                            headers=headers,
                            rows=rows,
                            row_offset=2,
                        )
                    )
        output = CanonicalTableOutput(
            tables=tables,
            metrics={"table_count": len(tables)},
            provenance={"file_name": path.name},
        )
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="pdf_read_tables",
                details={"table_count": len(tables)},
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("pdfplumber"),
            outputs={"table_output": output.model_dump(mode="json")},
            warnings=[],
            evidence=evidence,
            metrics=ToolMetrics(
                tables=len(tables), adapter_library_versions=library_versions("pdfplumber")
            ),
        )


class PdfManipulateTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        path = resolve_input_file(payload, context)
        operation = str(payload.get("operation", "rotate"))
        reader = _reader(path)
        writer = PdfWriter()
        if operation == "rotate":
            rotation = _optional_int(payload.get("rotation"), 90)
            for page in reader.pages:
                page.rotate(rotation)
                writer.add_page(page)
        elif operation == "split":
            pages = _pages_list(payload.get("pages"))
            if not pages:
                raise InputValidationError("Split operation requires pages.")
            for page_number in pages:
                writer.add_page(reader.pages[page_number - 1])
        else:
            raise InputValidationError(
                "Unsupported PDF manipulation operation.", details={"operation": operation}
            )
        stage = collector.stage_path("pdf_manipulate_output.pdf")
        with stage.open("wb") as handle:
            writer.write(handle)
        artifact = collector.commit(
            StagedArtifact(
                temp_path=stage,
                final_name="pdf_manipulate_output.pdf",
                media_type="application/pdf",
            )
        )
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="pdf_manipulate",
                details={"operation": operation, "artifact_name": artifact.name},
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("pypdf"),
            outputs={"artifact_path": artifact.path},
            warnings=[],
            evidence=evidence,
            metrics=ToolMetrics(
                pages=len(writer.pages),
                bytes_written=artifact.size_bytes,
                adapter_library_versions=library_versions("pypdf"),
            ),
            artifacts=[artifact],
        )


class PdfScannedDetectTool(ToolAdapter):
    def execute(self, payload: dict[str, object], context, collector: ArtifactCollector):
        path = resolve_input_file(payload, context)
        classification = _classify_pdf(path)
        mapped = "image_based" if classification == "ocr_required" else classification
        if mapped == "image_based":
            mapped = "ocr_required"
        evidence = [
            ToolEvidence(
                evidence_id=f"evidence-{uuid4().hex}",
                kind="pdf_scanned_detect",
                details={"classification": mapped},
            )
        ]
        return finalize_result(
            context=context,
            adapter_version="0.1.0",
            packages=library_versions("pdfplumber"),
            outputs={"classification": mapped},
            warnings=[],
            evidence=evidence,
            metrics=ToolMetrics(pages=1, adapter_library_versions=library_versions("pdfplumber")),
        )


def register_pdf_tools(registry) -> None:
    common_capability = ToolCapability(
        name="pdf_io",
        supported_formats=[".pdf"],
        supported_modes=["inspect", "read_text", "read_tables", "manipulate", "scanned_detect"],
        limits={"max_file_size_bytes": 50_000_000, "max_pages": 1000},
        deterministic=True,
        network_requirement=NetworkPolicy.DENY,
        known_fidelity_restrictions=["No OCR in v1", "Table extraction depends on PDF structure"],
    )
    for tool_key, adapter in [
        ("pdf_inspect", PdfInspectTool()),
        ("pdf_read_text", PdfReadTextTool()),
        ("pdf_read_tables", PdfReadTablesTool()),
        ("pdf_manipulate", PdfManipulateTool()),
        ("pdf_scanned_detect", PdfScannedDetectTool()),
    ]:
        registry.register(
            ToolRegistration(
                identity=ToolIdentity(
                    tool_key=tool_key,
                    version="0.1.0",
                    family="pdf",
                    adapter_key=f"pacca_tools.io.{tool_key}",
                ),
                capabilities=[common_capability],
                maturity=ToolMaturity.CERTIFIED,
                certification=CertificationVerdict.CERTIFIED,
                adapter=adapter,
            )
        )
