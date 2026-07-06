# cycling — Kommissärs Helferlein

Werkzeuge (Python-Scripte und ggf. Weboberflächen) für die Arbeit als Kommissär
bei Radsportveranstaltungen.

## Stack

- **Package Manager:** [uv](https://docs.astral.sh/uv/)
- **Python:** 3.14+
- **CLI:** cyclopts
- **Daten:** pandas + openpyxl

## Installation

```bash
uv sync
```

## Werkzeuge

### `html-to-excel`

Überführt alle HTML-Ergebnisdateien eines Verzeichnisses in eine einzelne
Excel-Datei. Je HTML-Datei entsteht ein Arbeitsblatt (Sheet), das den Inhalt
der Datei enthält (Tabellen werden mit pandas ausgelesen; enthält eine Datei
keine Tabelle, wird ihr Text übernommen).

```bash
uv run cycling html-to-excel /pfad/zu/html-dateien --output ergebnisse.xlsx
```

Argumente:

- `input_dir` — Verzeichnis mit den HTML-Dateien (`.html`/`.htm`).
- `--output` / `-o` — Zieldatei (Standard: `ergebnisse.xlsx`).

## Entwicklung

```bash
uv run pytest        # Tests
uv run mypy src      # Typprüfung
```
