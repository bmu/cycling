"""CLI interface for cycling tools using cyclopts."""

from pathlib import Path
from typing import Annotated

import cyclopts

app = cyclopts.App(
    name="cycling",
    help="Kommissärs Helferlein — Werkzeuge für Radsport-Kommissäre.",
)


@app.command(name="html-to-excel")
def html_to_excel(
    input_dir: Annotated[
        Path,
        cyclopts.Parameter(help="Verzeichnis mit den HTML-Ergebnisdateien."),
    ],
    *,
    output: Annotated[
        Path,
        cyclopts.Parameter(
            name=["--output", "-o"],
            help="Pfad der zu erzeugenden Excel-Datei.",
        ),
    ] = Path("ergebnisse.xlsx"),
) -> None:
    """HTML-Ergebnisdateien eines Verzeichnisses in eine Excel-Datei überführen.

    Je HTML-Datei wird ein Arbeitsblatt (Sheet) mit deren Inhalt erzeugt.
    """
    from cycling.html_to_excel import convert_directory

    try:
        result = convert_directory(input_dir, output)
    except (NotADirectoryError, FileNotFoundError) as exc:
        print(f"Fehler: {exc}")
        raise SystemExit(1) from exc

    print(f"\n🎉 Fertig: {result}")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
