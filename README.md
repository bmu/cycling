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

## Werkzeuge (intern)

### `tools/anonymize_results.py`

Bereitet echte HTML-Ergebnisdateien als anonymisierte Testfixtures auf: Personen
(Name, UCI-ID) und Vereine werden konsistent durch Fantasiewerte ersetzt,
Event-/Orts-/Verbandsbezüge neutralisiert. Optional werden Fake-PDFs mit gleichen
Basennamen erzeugt (Filter-Test). Die anonymisierten Fixtures liegen unter
`tests/fixtures/html_results/`.

```bash
uv run python tools/anonymize_results.py <quell-ordner> tests/fixtures/html_results
uv run python tools/anonymize_results.py <quell-ordner> <ziel> --no-pdf
```

> Hinweis: Echte, nicht-anonymisierte Ergebnisdateien gehören **nicht** ins Repo.

## Entwicklung

```bash
uv run pytest        # Tests
uv run mypy src      # Typprüfung
```
