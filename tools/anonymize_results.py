"""Anonymisiert echte HTML-Ergebnisdateien für die Verwendung als Testfixtures.

Der Ergebnis-Export der Zeitmessung (Tabelle ``class="points"`` mit den Spalten
Pos., St.Nr., UCI-ID, Nachname, Vorname, Verein, Runden, Gesamtzeit, Diff.) wird
so umgeschrieben, dass keine personenbezogenen Daten und keine Bezüge zum echten
Rennen übrig bleiben:

- Personen (Nachname, Vorname, UCI-ID) werden konsistent über alle Dateien durch
  Fantasiewerte ersetzt — dieselbe echte Person erhält überall dieselbe Fake-Identität.
- Vereine werden konsistent ersetzt.
- Event-Bezüge (Titel/Ort, Verband, Erstellungsdatum) werden neutralisiert.
- Optional werden Fake-PDFs mit gleichen Basennamen erzeugt, um zu testen, dass
  ein Konverter nur die HTML-Dateien findet.

Die Fake-Namenspools werden vor der Zuordnung so gefiltert, dass sie keinen echten
Namens-Token als Teilstring enthalten — damit gelangt garantiert kein echter Name
in die Ausgabe.

Aufruf:

    uv run python tools/anonymize_results.py <quell-ordner> <ziel-ordner>
    uv run python tools/anonymize_results.py <quell-ordner> <ziel-ordner> --no-pdf
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import cyclopts
from bs4 import BeautifulSoup, Tag

app = cyclopts.App(
    name="anonymize-results",
    help="HTML-Ergebnisdateien für Testfixtures anonymisieren.",
)

# --- Fake-Pools (rein erfunden, keine realen Personen/Orte) -----------------
FIRST = [
    "Alex", "Bea", "Chris", "Dana", "Emil", "Frida", "Gustav", "Hanna",
    "Ingo", "Jana", "Kai", "Lena", "Mats", "Nina", "Ole", "Pia",
    "Quirin", "Rosa", "Sven", "Tara", "Uwe", "Vera", "Wim", "Xenia",
    "Yannis", "Zoe", "Bruno", "Clara", "Doris", "Enno", "Feli", "Gero",
    "Heidi", "Ivo", "Jonas", "Karla", "Linus", "Mila", "Nils", "Olga",
]
LAST = [
    "Ahorn", "Birke", "Cedern", "Distel", "Erle", "Fichte", "Ginster",
    "Hasel", "Iris", "Jasmin", "Kiefer", "Linde", "Mohn", "Nessel",
    "Olive", "Pappel", "Quitte", "Rose", "Salbei", "Tanne", "Ulme",
    "Veilchen", "Weide", "Ysop", "Zeder", "Ahle", "Buche", "Ceder",
    "Dattel", "Efeu", "Farn", "Ginkgo", "Holler", "Ilex", "Jute",
    "Klee", "Lärche", "Malve", "Nelke", "Ohr",
]
CITIES = [
    "Musterhausen", "Beispieldorf", "Testheim", "Fabelstadt", "Nirgendbach",
    "Kleinweiler", "Grünau", "Sonnental", "Windeck", "Talheim",
    "Bergstetten", "Seeblick", "Auental", "Rosenberg", "Lindfeld",
    "Eichwald", "Steinfurt", "Moosbach", "Feldkirch", "Ottenau",
]
CLUB_PREFIX = ["RSV", "RV", "RC", "VC", "Team", "MTB", "SV", "SC"]

# Ersatzwerte für die Event-Bezüge.
FAKE_EVENT = "12. Radrenntag in Musterhausen Musterhausen"
FAKE_FEDERATION = "Musterland Radsportverband"
FAKE_CREATED = "erstellt von  01.01.2026 10:00"

PersonMap = dict[tuple[str, str], tuple[str, str]]


def _tokens(values: set[str]) -> set[str]:
    """Alle Wort-Tokens (>=3 Zeichen) aus den Strings, kleingeschrieben."""
    out: set[str] = set()
    for v in values:
        for tok in v.replace(".", " ").replace("-", " ").split():
            if len(tok) >= 3:
                out.add(tok.lower())
    return out


def _filter_pool(pool: list[str], forbidden: set[str]) -> list[str]:
    """Behalte nur Fake-Werte, die keinen echten Token als Teilstring enthalten
    (und umgekehrt) — damit die Ausgabe garantiert keinen echten Namen enthält."""
    safe: list[str] = []
    for cand in pool:
        cl = cand.lower()
        if any(tok in cl or cl in tok for tok in forbidden):
            continue
        safe.append(cand)
    return safe


def _result_table(soup: BeautifulSoup) -> Tag | None:
    """Die Ergebnis-Tabelle (``class="points"``) einer Seite, falls vorhanden."""
    tbl = soup.find("table", class_="points")
    return tbl if isinstance(tbl, Tag) else None


def _parse_table(tbl: Tag) -> tuple[dict[str, int], list[list[Tag]]]:
    """Spaltenindex (Name → Position) und Datenzeilen als Zell-Listen."""
    rows = [r for r in tbl.find_all("tr") if isinstance(r, Tag)]
    header = [th.get_text(strip=True) for th in rows[0].find_all("th")]
    idx = {name: i for i, name in enumerate(header)}
    data = [[c for c in r.find_all("td") if isinstance(c, Tag)] for r in rows[1:]]
    return idx, data


def build_maps(html_files: list[Path]) -> tuple[PersonMap, dict[str, str], dict[str, str]]:
    """Konsistente Zuordnungen für Personen, Vereine und UCI-IDs aufbauen."""
    persons: set[tuple[str, str]] = set()
    clubs: set[str] = set()
    ucis: set[str] = set()
    for path in html_files:
        tbl = _result_table(BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser"))
        if tbl is None:
            continue
        idx, data = _parse_table(tbl)
        for cells in data:
            if len(cells) < len(idx):
                continue
            persons.add(
                (
                    cells[idx["Nachname"]].get_text(strip=True),
                    cells[idx["Vorname"]].get_text(strip=True),
                )
            )
            clubs.add(cells[idx["Verein"]].get_text(strip=True))
            ucis.add(cells[idx["UCI-ID"]].get_text(strip=True))

    name_tokens = _tokens({p[0] for p in persons} | {p[1] for p in persons})
    firsts = _filter_pool(FIRST, name_tokens)
    lasts = _filter_pool(LAST, name_tokens)
    if len(firsts) < 5 or len(lasts) < 20:
        raise RuntimeError(
            f"Fake-Pools zu klein nach Filter: {len(firsts)} Vor-, {len(lasts)} Nachnamen"
        )

    person_map: PersonMap = {}
    for i, person in enumerate(sorted(persons)):
        first = firsts[i % len(firsts)]
        last = lasts[(i // len(firsts)) % len(lasts)]
        block = i // (len(firsts) * len(lasts))
        if block:  # Bei Überlauf Suffix anhängen, damit eindeutig.
            last = f"{last}{block}"
        person_map[person] = (last, first)

    club_map: dict[str, str] = {"": ""}
    for i, club in enumerate(sorted(c for c in clubs if c)):
        prefix = CLUB_PREFIX[i % len(CLUB_PREFIX)]
        city = CITIES[i % len(CITIES)]
        suffix = i // len(CITIES)
        club_map[club] = f"{prefix} {city}" + (f" {suffix + 1}" if suffix else "")

    uci_map: dict[str, str] = {}
    counter = 1
    for uci in sorted(ucis):
        if uci.strip():
            uci_map[uci] = f"1010{counter:07d}"
            counter += 1
        else:
            uci_map[uci] = uci

    return person_map, club_map, uci_map


def anonymize_html(
    path: Path,
    person_map: PersonMap,
    club_map: dict[str, str],
    uci_map: dict[str, str],
) -> str:
    """Eine Datei anonymisieren und den neuen HTML-Text zurückgeben."""
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")

    for div in soup.find_all("div", class_="headerbig"):
        div.string = FAKE_EVENT
    for div in soup.find_all("div", class_="footer"):
        div.string = FAKE_FEDERATION
    for div in soup.find_all("div", class_="save"):
        div.string = FAKE_CREATED

    tbl = _result_table(soup)
    if tbl is not None:
        idx, data = _parse_table(tbl)
        for cells in data:
            if len(cells) < len(idx):
                continue
            nach = cells[idx["Nachname"]].get_text(strip=True)
            vor = cells[idx["Vorname"]].get_text(strip=True)
            club = cells[idx["Verein"]].get_text(strip=True)
            uci = cells[idx["UCI-ID"]].get_text(strip=True)
            fake_nach, fake_vor = person_map[(nach, vor)]
            cells[idx["Nachname"]].string = fake_nach
            cells[idx["Vorname"]].string = fake_vor
            cells[idx["Verein"]].string = club_map.get(club, "")
            cells[idx["UCI-ID"]].string = uci_map.get(uci, uci)

    return str(soup)


def fake_pdf(title: str) -> bytes:
    """Minimales, gültiges einseitiges PDF mit Platzhaltertext erzeugen."""
    text = f"Fake-PDF fuer Tests - {title}"
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 120] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\nBT /F1 12 Tf 20 60 Td (%s) Tj ET\nendstream"
        % (len(text) + 30, text.encode("latin-1", "replace")),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets: list[int] = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (i, body)
    xref_pos = len(out)
    out += b"xref\n0 %d\n" % (len(objs) + 1)
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objs) + 1,
        xref_pos,
    )
    return out


@app.default
def run(
    source: Annotated[Path, cyclopts.Parameter(help="Ordner mit den echten HTML-Dateien.")],
    target: Annotated[Path, cyclopts.Parameter(help="Zielordner für die anonymisierten Dateien.")],
    *,
    pdf: Annotated[
        bool,
        cyclopts.Parameter(help="Zusätzlich Fake-PDFs mit gleichen Basennamen erzeugen."),
    ] = True,
) -> None:
    """Alle HTML-Dateien aus ``source`` anonymisiert nach ``target`` schreiben."""
    if not source.is_dir():
        print(f"Fehler: Kein Verzeichnis: {source}")
        raise SystemExit(1)

    html_files = sorted(source.glob("*.html"))
    if not html_files:
        print(f"Fehler: Keine HTML-Dateien in {source}")
        raise SystemExit(1)

    target.mkdir(parents=True, exist_ok=True)
    person_map, club_map, uci_map = build_maps(html_files)

    for path in html_files:
        (target / path.name).write_text(
            anonymize_html(path, person_map, club_map, uci_map), encoding="utf-8"
        )
        if pdf:
            (target / f"{path.stem}.pdf").write_bytes(fake_pdf(path.stem))

    print(
        f"✓ {len(html_files)} HTML anonymisiert"
        + (f" + {len(html_files)} Fake-PDF" if pdf else "")
        + f" → {target}"
    )
    print(
        f"  Personen: {len(person_map)}, Vereine: {len(club_map) - 1}, "
        f"UCI-IDs: {sum(1 for v in uci_map.values() if v.strip())}"
    )


if __name__ == "__main__":
    app()
