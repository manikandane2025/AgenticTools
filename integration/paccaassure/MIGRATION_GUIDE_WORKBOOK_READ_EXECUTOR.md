# Migration Guide From Metadata-Only `WorkbookReadExecutor`

1. Install `paccaassure-common-tools==0.1.0`.
2. Import the generated tool manifest into the Global Tool Catalog.
3. Activate `excel_read` version `0.1.0` for the target environment.
4. Replace the legacy workbook handler with a thin runtime adapter that constructs `ToolInvocation`.
5. Map workbook snapshot input into the package `path` payload field.
6. Consume canonical `table_output` rather than workbook metadata.
7. Preserve the previous workflow version for rollback until the certified path is proven in runtime.
