"""Convert a directory of HTML result files into a single Excel workbook.

Each input HTML file becomes one worksheet whose content mirrors the HTML file.
Tables are read with :mod:`pandas` (``read_html``). If a file contains no
tables, its visible text is used as a fallback so that no input is silently
dropped — the guarantee is: one sheet per HTML input.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from cycling.logging import get_logger

# Characters Excel forbids in worksheet names.
_FORBIDDEN_SHEET_CHARS = re.compile(r"[:\\/?*\[\]]")
# Excel worksheet names are limited to 31 characters.
_MAX_SHEET_NAME_LEN = 31
# Blank rows inserted between multiple tables stacked on one sheet.
_TABLE_GAP = 1

HTML_SUFFIXES = (".html", ".htm")


def sanitize_sheet_name(name: str, used: set[str]) -> str:
    """Return an Excel-safe, unique worksheet name derived from ``name``.

    Args:
        name: Desired sheet name (typically the HTML file stem).
        used: Names already assigned; the returned name is added to it.
    """
    cleaned = _FORBIDDEN_SHEET_CHARS.sub("_", name).strip()
    # Excel also forbids a name wrapped in single quotes and the name "History".
    cleaned = cleaned.strip("'") or "Sheet"
    if cleaned.lower() == "history":
        cleaned = "History_"
    cleaned = cleaned[:_MAX_SHEET_NAME_LEN]

    candidate = cleaned
    counter = 2
    while candidate.lower() in {u.lower() for u in used}:
        suffix = f"_{counter}"
        candidate = cleaned[: _MAX_SHEET_NAME_LEN - len(suffix)] + suffix
        counter += 1

    used.add(candidate)
    return candidate


def tables_from_html(html: str) -> list[pd.DataFrame]:
    """Read all tables from an HTML string as DataFrames.

    Returns an empty list if the string contains no parseable tables.
    """
    try:
        return pd.read_html(io.StringIO(html))
    except ValueError:
        # pandas raises ValueError("No tables found") when there is no table.
        return []


def text_from_html(html: str) -> pd.DataFrame:
    """Fallback: extract visible text from an HTML string into a single column."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    lines = [line.strip() for line in soup.get_text("\n").splitlines() if line.strip()]
    return pd.DataFrame({"Inhalt": lines})


def read_html_tables(path: Path) -> list[pd.DataFrame]:
    """Read all tables from an HTML file as DataFrames."""
    return tables_from_html(path.read_text(encoding="utf-8", errors="replace"))


def read_html_text(path: Path) -> pd.DataFrame:
    """Fallback: extract visible text from an HTML file into a single column."""
    return text_from_html(path.read_text(encoding="utf-8", errors="replace"))


def find_html_files(input_dir: Path) -> list[Path]:
    """Return sorted HTML files directly inside ``input_dir``."""
    files = [
        p
        for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in HTML_SUFFIXES
    ]
    return sorted(files)


def _write_sheet(
    writer: pd.ExcelWriter,
    sheet_name: str,
    tables: list[pd.DataFrame],
) -> None:
    """Write one or more tables stacked vertically onto a single sheet."""
    start_row = 0
    for table in tables:
        table.to_excel(
            writer,
            sheet_name=sheet_name,
            index=False,
            startrow=start_row,
        )
        # +1 for the header row that to_excel writes.
        start_row += len(table) + 1 + _TABLE_GAP


def convert_html_sources(
    sources: list[tuple[str, str]],
    output: Path | BinaryIO,
) -> int:
    """Write one worksheet per HTML source into an Excel workbook.

    Args:
        sources: ``(name, html)`` pairs — ``name`` becomes the sheet name (its
            stem is used), ``html`` is the file's HTML content.
        output: Destination path or writable binary stream for the ``.xlsx``.

    Returns:
        The number of worksheets written.

    Raises:
        ValueError: If ``sources`` is empty.
    """
    if not sources:
        raise ValueError("Keine HTML-Quellen übergeben")

    logger = get_logger()
    logger.step(f"Konvertiere {len(sources)} HTML-Datei(en)")

    used_names: set[str] = set()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, html in sources:
            tables = tables_from_html(html)
            if tables:
                detail = f"{len(tables)} Tabelle(n)"
            else:
                tables = [text_from_html(html)]
                detail = "kein Tabelleninhalt, Text übernommen"

            sheet_name = sanitize_sheet_name(Path(name).stem, used_names)
            _write_sheet(writer, sheet_name, tables)
            logger.substep(f"{name} → Sheet '{sheet_name}' ({detail})")

    return len(sources)


def convert_directory(input_dir: Path, output: Path) -> Path:
    """Convert every HTML file in ``input_dir`` into one sheet of ``output``.

    Args:
        input_dir: Directory containing the HTML result files.
        output: Path of the ``.xlsx`` file to create.

    Returns:
        The path to the written workbook.

    Raises:
        NotADirectoryError: If ``input_dir`` is not a directory.
        FileNotFoundError: If no HTML files are found in ``input_dir``.
    """
    logger = get_logger()

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Kein Verzeichnis: {input_dir}")

    html_files = find_html_files(input_dir)
    if not html_files:
        raise FileNotFoundError(
            f"Keine HTML-Dateien ({', '.join(HTML_SUFFIXES)}) in {input_dir} gefunden"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    sources = [
        (path.name, path.read_text(encoding="utf-8", errors="replace"))
        for path in html_files
    ]
    convert_html_sources(sources, output)

    logger.success(f"Excel-Datei erstellt: {output}")
    return output
