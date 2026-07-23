# Excel, CSV, and PDF Detailed Requirements

## Excel

### Supported formats

- `.xlsx`
- `.xlsm` read support
- `.xls` explicitly unsupported in v1 unless separate adapter is added

### excel_inspect

Must return:

- workbook properties
- sheet list/order
- visible/hidden state
- active sheet
- dimensions
- header candidates
- sample rows
- formulas count
- merged ranges
- named ranges
- Excel table definitions
- comments/hyperlinks counts
- warnings
- metrics

### excel_read

Must support:

- one/all selected sheets
- explicit header row
- automatic header detection with confidence
- explicit cell range
- read-only streaming
- formula text
- cached values when available
- date/time normalization
- number/boolean/string/error/blank types
- merged-cell policy
- blank-row policy
- duplicate-header policy
- hidden row/column policy
- source row/cell provenance
- row limit
- sheet limit
- file-size limit
- deterministic output

Must not silently return empty rows when parsing fails.

### excel_validate

- valid type/signature
- corruption
- encryption/password
- sheet required
- required headers
- duplicate headers
- row/column count
- schema
- size
- formulas policy
- unsupported-feature warnings

### excel_write

- multiple sheets
- typed rows
- formulas
- tables
- freeze panes
- widths/heights
- styles
- number/date formats
- conditional formatting
- validation
- comments
- hyperlinks
- images
- charts
- streaming/constant-memory mode
- artifact/evidence

### excel_compare

- sheets
- dimensions
- headers
- rows
- values
- formulas
- typed diff
- configurable keys

### excel_edit_existing

- separate capability
- fidelity report mandatory
- never overwrite immutable input
- create new artifact
- report unsupported round-trip objects

### Excel fixtures

- normal 100-row workbook
- multiple sheets
- hidden sheet
- merged cells
- formulas
- dates
- duplicate headers
- blank rows
- empty workbook
- corrupt workbook
- encrypted workbook
- large workbook
- macros
- unsupported objects

## CSV

### csv_inspect

- encoding
- delimiter
- quote/escape
- header confidence
- line count estimate
- malformed rows
- sample rows

### csv_read

- explicit/auto dialect
- explicit/auto encoding
- header/no-header
- streaming
- schema
- malformed-row policy
- line provenance
- record limits
- deterministic canonical tables

### csv_validate

- encoding
- dialect
- row shape
- required headers
- schema
- size
- duplicate headers
- malformed lines

### csv_write

- encoding
- delimiter
- quoting
- newline policy
- headers
- deterministic ordering
- artifact/evidence

### CSV fixtures

- comma/tab/pipe/semicolon
- quoted delimiters
- embedded newlines
- UTF-8/UTF-16
- no header
- malformed rows
- huge file
- empty file

## PDF

### pdf_inspect

- metadata
- page count
- encryption
- dimensions
- rotation
- text availability
- scanned/mixed status
- image count
- table candidates

### pdf_read_text

- page text
- page provenance
- words/positions when available
- reading-order warnings
- page selection
- size/page limits

### pdf_read_tables

- table candidates
- page coordinates
- rows/cells
- confidence/warnings
- canonical tables

### pdf_manipulate

- split
- merge
- rotate
- crop
- metadata update
- output artifact

### pdf_scanned_detect

Returns:

- text_based
- image_based
- mixed
- ocr_required

### PDF errors

- encrypted without credential
- corrupt
- malformed xref
- no extractable text
- unsupported security
- limits exceeded

### PDF fixtures

- text PDF
- table PDF
- multi-page
- rotated
- encrypted
- scanned
- mixed
- corrupt
- very large
