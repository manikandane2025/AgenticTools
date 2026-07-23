# Tool Contracts and Schemas

## Tool Identity

```json
{
  "tool_key": "excel_read",
  "version": "1.0.0",
  "family": "format_reader",
  "adapter_key": "pacca_tools.io.excel.read",
  "execution_placement": "shared_runtime"
}
```

## Invocation

```json
{
  "tool_invocation_id": "tinv-...",
  "runtime_run_id": "run-...",
  "node_attempt_id": "attempt-...",
  "tool": {
    "tool_key": "excel_read",
    "version": "1.0.0",
    "adapter_key": "pacca_tools.io.excel.read"
  },
  "context": {
    "tenant_id": "tenant",
    "project_id": "project",
    "environment_id": "environment",
    "input_snapshot_refs": ["ris-..."],
    "workspace": {
      "input_root": "/runtime/inputs",
      "output_root": "/runtime/output",
      "temp_root": "/runtime/tmp"
    }
  },
  "input_payload": {},
  "policy_snapshot": {},
  "idempotency_key": "..."
}
```

## Result

```json
{
  "status": "completed",
  "outputs": {},
  "artifacts": [],
  "evidence": [],
  "warnings": [],
  "errors": [],
  "metrics": {},
  "provenance": {}
}
```

## Error

```json
{
  "code": "TOOL_FILE_CORRUPT",
  "message": "The workbook could not be opened.",
  "category": "input",
  "retryable": false,
  "safe_details": {
    "file_name": "input.xlsx"
  },
  "cause_reference": "log-ref"
}
```

## Canonical Table Model

```json
{
  "tables": [
    {
      "table_id": "tbl-1",
      "name": "Sheet1",
      "source": {
        "type": "excel",
        "file_name": "input.xlsx",
        "sheet_name": "Sheet1"
      },
      "columns": [
        {
          "name": "ID",
          "normalized_name": "id",
          "ordinal": 1,
          "data_type": "string"
        }
      ],
      "rows": [
        {
          "row_number": 2,
          "values": {
            "id": "A-001"
          }
        }
      ]
    }
  ],
  "warnings": [],
  "metrics": {},
  "provenance": {}
}
```

## Canonical Document Model

```json
{
  "document": {
    "metadata": {},
    "sections": [],
    "pages": [],
    "tables": [],
    "links": [],
    "images": []
  },
  "warnings": [],
  "metrics": {},
  "provenance": {}
}
```

## Capability Manifest

Every capability includes:

- supported formats
- supported modes
- limits
- deterministic status
- network requirement
- filesystem requirement
- credential requirement
- runtime compatibility
- known fidelity restrictions

## Versioning

- patch: backward-compatible fix
- minor: additive capability
- major: breaking contract

Published workflows seal exact versions unless an approved compatible-range policy is explicitly enabled.
