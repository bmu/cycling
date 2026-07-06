"""User-friendly logging for cycling tools."""

import logging
import sys
from dataclasses import dataclass, field


@dataclass
class ToolLogger:
    """Logger for user-friendly progress updates."""

    _logger: logging.Logger = field(init=False)

    def __post_init__(self) -> None:
        self._logger = logging.getLogger("cycling")
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def info(self, message: str) -> None:
        self._logger.info(f"→ {message}")

    def success(self, message: str) -> None:
        self._logger.info(f"✓ {message}")

    def warning(self, message: str) -> None:
        self._logger.warning(f"⚠ {message}")

    def step(self, step_name: str) -> None:
        self._logger.info(f"\n▸ {step_name}...")

    def substep(self, message: str) -> None:
        self._logger.info(f"  {message}")


_logger: ToolLogger | None = None


def get_logger() -> ToolLogger:
    """Get the global tool logger."""
    global _logger
    if _logger is None:
        _logger = ToolLogger()
    return _logger


def reset_logger() -> None:
    """Reset the logger (useful for testing)."""
    global _logger
    _logger = None
