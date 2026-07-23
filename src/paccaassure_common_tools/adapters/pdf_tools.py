from __future__ import annotations

from pathlib import Path
from typing import Any

import pdfplumber
from pypdf import PdfReader, PdfWriter

from paccaassure_common_tools.adapters.common import (
    build_source_artifact,
    canonical_checksum,
    evidence,
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
    ToolIdentity,
    ToolInvocationContext,
    ToolMaturity,
    ToolMetrics,
    ToolRegistration,
    ToolResult,
)
from paccaassure_common_tools.version import PACKAGE_VERSION


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


def _source(path: Path) -> dict[str, object]:
    return build_source_artifact(path, media_type="application/pdf", detected_format=".pdf")


def _classify_pdf(path: Path) -> tuple[str, int, int]:
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
            return "mixed", text_pages, image_pages
        if image_pages and not text_pages:
            return "ocr_required", text_pages, image_pages
        return "text_based", text_pages, image_pages


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
    def execute(
        self,
        payload: dict[str, object],
        context: ToolInvocationContext,
        collector: ArtifactCollector,
    ) -> ToolResult:
        del collector
        path = resolve_input_file(payload, context)
        packages = library_versions("pypdf", "pdfplumber")
        reader = _reader(path)
        source = _source(path)
        classification, text_pages, image_pages = _classify_pdf(path)
        outputs = {
            "metadata": {key: str(value) for key, value in (reader.metadata or {}).items()},
            "page_count": len(reader.pages),
            "encrypted": reader.is_encrypted,
            "scanned_status": classification,
        }
        evidence_items = [
            evidence(
                context=context,
                kind="pdf_inspect",
                source_checksum=str(source["source_checksum"]),
                output_checksum=canonical_checksum(outputs),
                capability_ids=["pdf.inspect_metadata_and_classification"],
                details=outputs,
                source_artifact_ref=path.name,
                fixture_identity=path.name,
            )
        ]
        return finalize_result(
            context=context,
            packages=packages,
            outputs=outputs,
            warnings=[],
            evidence=evidence_items,
            metrics=ToolMetrics(
                input_bytes=path.stat().st_size,
                pages_discovered=len(reader.pages),
                pages_processed=len(reader.pages),
                text_pages=text_pages,
                image_pages=image_pages,
                adapter_library_versions=packages,
            ),
            capabilities_exercised=["pdf.inspect_metadata_and_classification"],
            source_artifacts=[source],
            policies={"ocr_execution": "deny"},
        )


class PdfReadTextTool(ToolAdapter):
    def execute(
        self,
        payload: dict[str, object],
        context: ToolInvocationContext,
        collector: ArtifactCollector,
    ) -> ToolResult:
        del collector
        path = resolve_input_file(payload, context)
        packages = library_versions("pdfplumber")
        source = _source(path)
        _reader(path)
        classification, text_pages, image_pages = _classify_pdf(path)
        if classification == "ocr_required":
            raise InputValidationError(
                "PDF is image-based and requires OCR.", details={"file_name": path.name}
            )
        page_selection = set(_pages_list(payload.get("pages")))
        pages = []
        with pdfplumber.open(str(path)) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                if page_selection and index not in page_selection:
                    continue
                pages.append(
                    {
                        "page_number": index,
                        "text": page.extract_text() or "",
                        "source": {"page_number": index, "rotation": page.rotation or 0},
                    }
                )
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
        outputs = {"document_output": output.model_dump(mode="json")}
        evidence_items = [
            evidence(
                context=context,
                kind="pdf_read_text",
                source_checksum=str(source["source_checksum"]),
                output_checksum=canonical_checksum(outputs),
                capability_ids=["pdf.read_page_text"],
                details={"page_count": len(pages)},
                source_artifact_ref=path.name,
                fixture_identity=path.name,
            )
        ]
        return finalize_result(
            context=context,
            packages=packages,
            outputs=outputs,
            warnings=[],
            evidence=evidence_items,
            metrics=ToolMetrics(
                input_bytes=path.stat().st_size,
                pages_discovered=text_pages + image_pages,
                pages_processed=len(pages),
                text_pages=text_pages,
                image_pages=image_pages,
                adapter_library_versions=packages,
            ),
            capabilities_exercised=["pdf.read_page_text"],
            source_artifacts=[source],
            selection={"pages": sorted(page_selection) if page_selection else "all"},
            policies={"ocr_execution": "deny"},
        )


class PdfReadTablesTool(ToolAdapter):
    def execute(
        self,
        payload: dict[str, object],
        context: ToolInvocationContext,
        collector: ArtifactCollector,
    ) -> ToolResult:
        del collector
        path = resolve_input_file(payload, context)
        packages = library_versions("pdfplumber")
        source = _source(path)
        tables = []
        pages_processed = 0
        with pdfplumber.open(str(path)) as pdf:
            for page_index, page in enumerate(pdf.pages, start=1):
                pages_processed += 1
                extracted = page.extract_tables()
                for table_index, table in enumerate(extracted, start=1):
                    if not table or not table[0]:
                        continue
                    headers = [cell or f"column_{i+1}" for i, cell in enumerate(table[0])]
                    rows = table[1:]
                    def row_source(
                        row_number: int,
                        _width: int,
                        *,
                        page_number: int = page_index,
                        table_number: int = table_index,
                    ) -> dict[str, object]:
                        return {
                            "page_number": page_number,
                            "table_index": table_number,
                            "source_checksum": source["source_checksum"],
                        }
                    tables.append(
                        rows_to_canonical_table(
                            name=f"page_{page_index}_table_{table_index}",
                            source={"type": "pdf", "file_name": path.name, "page_number": page_index},
                            headers=headers,
                            rows=rows,
                            row_offset=2,
                            source_builder=row_source,
                        )
                    )
        output = CanonicalTableOutput(
            tables=tables,
            metrics={"table_count": len(tables)},
            provenance={"file_name": path.name},
        )
        outputs = {"table_output": output.model_dump(mode="json")}
        evidence_items = [
            evidence(
                context=context,
                kind="pdf_read_tables",
                source_checksum=str(source["source_checksum"]),
                output_checksum=canonical_checksum(outputs),
                capability_ids=["pdf.read_detected_tables"],
                details={"table_count": len(tables)},
                source_artifact_ref=path.name,
                fixture_identity=path.name,
            )
        ]
        return finalize_result(
            context=context,
            packages=packages,
            outputs=outputs,
            warnings=[],
            evidence=evidence_items,
            metrics=ToolMetrics(
                input_bytes=path.stat().st_size,
                pages_processed=pages_processed,
                tables_detected=len(tables),
                tables_returned=len(tables),
                adapter_library_versions=packages,
            ),
            capabilities_exercised=["pdf.read_detected_tables"],
            source_artifacts=[source],
        )


class PdfManipulateTool(ToolAdapter):
    def execute(
        self,
        payload: dict[str, object],
        context: ToolInvocationContext,
        collector: ArtifactCollector,
    ) -> ToolResult:
        path = resolve_input_file(payload, context)
        packages = library_versions("pypdf")
        source = _source(path)
        operation = str(payload.get("operation", "rotate"))
        reader = _reader(path)
        writer = PdfWriter()
        capability_id = ""
        if operation == "rotate":
            capability_id = "pdf.rotate_pages"
            rotation = _optional_int(payload.get("rotation"), 90)
            for page in reader.pages:
                page.rotate(rotation)
                writer.add_page(page)
        elif operation == "split":
            capability_id = "pdf.split_selected_pages"
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
        evidence_items = [
            evidence(
                context=context,
                kind="pdf_manipulate",
                source_checksum=str(source["source_checksum"]),
                output_checksum=artifact.sha256,
                capability_ids=[capability_id],
                details={"operation": operation, "artifact_name": artifact.logical_name},
                source_artifact_ref=path.name,
                fixture_identity=path.name,
                artifact_refs=[artifact.logical_name],
            )
        ]
        artifact.evidence_ref = evidence_items[0].evidence_id
        return finalize_result(
            context=context,
            packages=packages,
            outputs={"artifact_path": artifact.path},
            warnings=[],
            evidence=evidence_items,
            metrics=ToolMetrics(
                input_bytes=path.stat().st_size,
                pages_processed=len(writer.pages),
                output_bytes_written=artifact.size_bytes,
                artifacts_created=1,
                adapter_library_versions=packages,
            ),
            capabilities_exercised=[capability_id],
            source_artifacts=[source],
            selection={"operation": operation},
            artifacts=[artifact],
        )


class PdfScannedDetectTool(ToolAdapter):
    def execute(
        self,
        payload: dict[str, object],
        context: ToolInvocationContext,
        collector: ArtifactCollector,
    ) -> ToolResult:
        del collector
        path = resolve_input_file(payload, context)
        packages = library_versions("pdfplumber")
        source = _source(path)
        classification, text_pages, image_pages = _classify_pdf(path)
        mapped = "image_based" if classification == "ocr_required" else classification
        if mapped == "image_based":
            mapped = "ocr_required"
        outputs = {"classification": mapped}
        evidence_items = [
            evidence(
                context=context,
                kind="pdf_scanned_detect",
                source_checksum=str(source["source_checksum"]),
                output_checksum=canonical_checksum(outputs),
                capability_ids=["pdf.classify_scan_state"],
                details={"classification": mapped},
                source_artifact_ref=path.name,
                fixture_identity=path.name,
            )
        ]
        return finalize_result(
            context=context,
            packages=packages,
            outputs=outputs,
            warnings=[],
            evidence=evidence_items,
            metrics=ToolMetrics(
                input_bytes=path.stat().st_size,
                pages_processed=text_pages + image_pages,
                text_pages=text_pages,
                image_pages=image_pages,
                ocr_required_pages=image_pages if mapped == "ocr_required" else 0,
                adapter_library_versions=packages,
            ),
            capabilities_exercised=["pdf.classify_scan_state"],
            source_artifacts=[source],
            policies={"ocr_execution": "deny"},
        )


def register_pdf_tools(registry: Any) -> None:
    registrations: list[tuple[str, ToolAdapter, list[ToolCapability]]] = [
        (
            "pdf_inspect",
            PdfInspectTool(),
            [
                ToolCapability(
                    name="pdf.inspect_metadata_and_classification",
                    supported_formats=[".pdf"],
                    supported_modes=["inspect"],
                    limits={"max_file_size_bytes": 50_000_000, "max_pages": 1000},
                    deterministic=True,
                    network_requirement=NetworkPolicy.DENY,
                    known_fidelity_restrictions=["No OCR in v1"],
                )
            ],
        ),
        (
            "pdf_read_text",
            PdfReadTextTool(),
            [
                ToolCapability(
                    name="pdf.read_page_text",
                    supported_formats=[".pdf"],
                    supported_modes=["read_text"],
                    limits={"max_file_size_bytes": 50_000_000, "max_pages": 1000},
                    deterministic=True,
                    network_requirement=NetworkPolicy.DENY,
                    known_fidelity_restrictions=["No OCR in v1"],
                )
            ],
        ),
        (
            "pdf_read_tables",
            PdfReadTablesTool(),
            [
                ToolCapability(
                    name="pdf.read_detected_tables",
                    supported_formats=[".pdf"],
                    supported_modes=["read_tables"],
                    limits={"max_file_size_bytes": 50_000_000, "max_pages": 1000},
                    deterministic=True,
                    network_requirement=NetworkPolicy.DENY,
                    known_fidelity_restrictions=["Table extraction depends on PDF structure"],
                )
            ],
        ),
        (
            "pdf_manipulate",
            PdfManipulateTool(),
            [
                ToolCapability(
                    name="pdf.rotate_pages",
                    supported_formats=[".pdf"],
                    supported_modes=["rotate"],
                    limits={"max_file_size_bytes": 50_000_000, "max_pages": 1000},
                    deterministic=True,
                    network_requirement=NetworkPolicy.DENY,
                ),
                ToolCapability(
                    name="pdf.split_selected_pages",
                    supported_formats=[".pdf"],
                    supported_modes=["split"],
                    limits={"max_file_size_bytes": 50_000_000, "max_pages": 1000},
                    deterministic=True,
                    network_requirement=NetworkPolicy.DENY,
                ),
            ],
        ),
        (
            "pdf_scanned_detect",
            PdfScannedDetectTool(),
            [
                ToolCapability(
                    name="pdf.classify_scan_state",
                    supported_formats=[".pdf"],
                    supported_modes=["scanned_detect"],
                    limits={"max_file_size_bytes": 50_000_000, "max_pages": 1000},
                    deterministic=True,
                    network_requirement=NetworkPolicy.DENY,
                    known_fidelity_restrictions=["No OCR in v1"],
                )
            ],
        ),
    ]
    for tool_key, adapter, capabilities in registrations:
        registry.register(
            ToolRegistration(
                identity=ToolIdentity(
                    tool_key=tool_key,
                    version=PACKAGE_VERSION,
                    family="pdf",
                    adapter_key=f"pacca_tools.io.{tool_key}",
                ),
                capabilities=capabilities,
                maturity=ToolMaturity.CERTIFIED,
                certification=CertificationVerdict.CERTIFIED,
                adapter=adapter,
            )
        )
