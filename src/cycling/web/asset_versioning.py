"""Cache-Busting für statische Assets via Content-Hash im ``?v=`` Query.

Ändert sich eine Datei, ändert sich der Hash und damit die URL — Browser laden
das Asset neu. Der Hash wird pro Pfad einmal berechnet (``functools.cache``).
"""

import hashlib
from functools import cache
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parent / "static"


@cache
def _asset_hash(path: str) -> str:
    """Die ersten 8 Hex-Zeichen des SHA-256 der Datei, oder "" wenn fehlend."""
    try:
        data = (STATIC_DIR / path).read_bytes()
    except OSError:
        return ""
    return hashlib.sha256(data).hexdigest()[:8]


def static_v(path: str) -> str:
    """Cache-gebustete ``/static/<path>?v=<hash>`` URL (bzw. ohne, wenn fehlend)."""
    h = _asset_hash(path)
    return f"/static/{path}?v={h}" if h else f"/static/{path}"
