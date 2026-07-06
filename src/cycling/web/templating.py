"""Zentrale Jinja2-Templates-Instanz mit registriertem ``static_v``-Global."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

from cycling.web.asset_versioning import static_v

templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")
templates.env.globals["static_v"] = static_v
