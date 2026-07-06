"""Tests for the HTML-to-Excel conversion."""

from pathlib import Path

import pandas as pd
import pytest
from openpyxl import load_workbook

from cycling.html_to_excel import convert_directory, sanitize_sheet_name


def test_sanitize_sheet_name_removes_forbidden_chars() -> None:
    used: set[str] = set()
    assert sanitize_sheet_name("Etappe 1/2 [A]", used) == "Etappe 1_2 _A_"


def test_sanitize_sheet_name_truncates_to_31() -> None:
    used: set[str] = set()
    name = sanitize_sheet_name("x" * 50, used)
    assert len(name) == 31


def test_sanitize_sheet_name_deduplicates() -> None:
    used: set[str] = set()
    first = sanitize_sheet_name("Ergebnis", used)
    second = sanitize_sheet_name("Ergebnis", used)
    assert first == "Ergebnis"
    assert second == "Ergebnis_2"


def _write_html_table(path: Path, df: pd.DataFrame) -> None:
    path.write_text(df.to_html(index=False), encoding="utf-8")


def test_convert_directory_one_sheet_per_file(tmp_path: Path) -> None:
    src = tmp_path / "html"
    src.mkdir()
    _write_html_table(
        src / "etappe1.html",
        pd.DataFrame({"Rang": [1, 2], "Fahrer": ["A", "B"]}),
    )
    _write_html_table(
        src / "etappe2.html",
        pd.DataFrame({"Rang": [1], "Fahrer": ["C"]}),
    )

    out = tmp_path / "out.xlsx"
    convert_directory(src, out)

    wb = load_workbook(out)
    assert set(wb.sheetnames) == {"etappe1", "etappe2"}
    assert wb["etappe1"]["B2"].value == "A"


def test_convert_directory_text_fallback(tmp_path: Path) -> None:
    src = tmp_path / "html"
    src.mkdir()
    (src / "notiz.html").write_text(
        "<html><body><p>Kein Tabelleninhalt hier</p></body></html>",
        encoding="utf-8",
    )

    out = tmp_path / "out.xlsx"
    convert_directory(src, out)

    wb = load_workbook(out)
    assert wb.sheetnames == ["notiz"]
    assert wb["notiz"]["A1"].value == "Inhalt"


def test_convert_directory_no_html_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        convert_directory(tmp_path, tmp_path / "out.xlsx")
