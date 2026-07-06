"""FastAPI-Anwendung für die Kommissärs-Weboberfläche."""

from __future__ import annotations

import io
import os
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from cycling.html_to_excel import HTML_SUFFIXES, convert_html_sources
from cycling.web.templating import templates

BASE_DIR = Path(__file__).resolve().parent
XLSX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
# Optionaler Link zur Datenschutzerklärung; beim Hosting per Env-Variable setzen.
PRIVACY_URL = os.environ.get("CYCLING_PRIVACY_URL") or None

app = FastAPI(title="Kommissärs Helferlein", docs_url=None, redoc_url=None, openapi_url=None)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Sicherheits-Header auf alle Antworten setzen."""
    response = await call_next(request)
    response.headers["Content-Language"] = "de"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; "
        "img-src 'self' data:; font-src 'self'; form-action 'self'; "
        "frame-ancestors 'none'; base-uri 'self'"
    )
    return response


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Startseite mit dem Upload-Formular."""
    return templates.TemplateResponse(
        request=request, name="index.html", context={"privacy_url": PRIVACY_URL}
    )


@app.post("/convert")
async def convert(request: Request, files: list[UploadFile]) -> Response:
    """Hochgeladene HTML-Dateien in eine Excel-Datei überführen.

    Je HTML-Datei entsteht ein Arbeitsblatt. Nicht-HTML-Dateien werden ignoriert.
    Bei Fehlern wird die Startseite mit einer Meldung erneut angezeigt.
    """
    sources: list[tuple[str, str]] = []
    for upload in files:
        name = upload.filename or ""
        if Path(name).suffix.lower() not in HTML_SUFFIXES:
            continue
        raw = await upload.read()
        sources.append((name, raw.decode("utf-8", errors="replace")))

    if not sources:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            status_code=400,
            context={
                "error": "Bitte mindestens eine HTML-Datei (.html/.htm) auswählen.",
                "privacy_url": PRIVACY_URL,
            },
        )

    buffer = io.BytesIO()
    convert_html_sources(sources, buffer)
    buffer.seek(0)

    return Response(
        content=buffer.getvalue(),
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": 'attachment; filename="ergebnisse.xlsx"'},
    )


def run() -> None:
    """Entwicklungsserver starten (Entry-Point ``cycling-web``)."""
    import uvicorn

    uvicorn.run("cycling.web.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    run()
