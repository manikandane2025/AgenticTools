from __future__ import annotations

import csv
from pathlib import Path

import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def create_excel() -> None:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    sheet.append(["ID", "Name", "Value"])
    for index in range(1, 121):
        sheet.append([f"A-{index:03d}", f"Row {index}", index])
    extra = workbook.create_sheet("HiddenSheet")
    extra.sheet_state = "hidden"
    extra.append(["Flag", "Status"])
    extra.append(["Y", "hidden"])
    workbook.save(ROOT / "normal_workbook.xlsx")

    dup = openpyxl.Workbook()
    dsheet = dup.active
    dsheet.append(["ID", "ID", "Value"])
    dsheet.append(["1", "duplicate", "x"])
    dup.save(ROOT / "duplicate_headers.xlsx")


def create_csv() -> None:
    rows = [["id", "name", "value"], ["1", "alpha", "100"], ["2", "beta", "200"]]
    with (ROOT / "comma_utf8.csv").open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(rows)
    with (ROOT / "semicolon_utf8.csv").open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, delimiter=";").writerows(rows)
    with (ROOT / "malformed.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "name", "value"])
        writer.writerow(["1", "broken"])


def create_text_pdf(path: Path, text: str) -> None:
    pdf = canvas.Canvas(str(path), pagesize=letter)
    pdf.drawString(72, 720, text)
    pdf.save()


def create_table_pdf(path: Path) -> None:
    pdf = canvas.Canvas(str(path), pagesize=letter)
    pdf.drawString(72, 760, "ID   NAME   VALUE")
    pdf.drawString(72, 740, "1    Alpha  10")
    pdf.drawString(72, 720, "2    Beta   20")
    pdf.save()


def create_fixtures() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    create_excel()
    create_csv()
    create_text_pdf(ROOT / "text.pdf", "PaccaAssure PDF text fixture")
    create_table_pdf(ROOT / "table.pdf")


if __name__ == "__main__":
    create_fixtures()
