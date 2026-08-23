from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DomainError(Exception):
    """An expected application failure that can be safely returned to clients."""

    code: str
    message: str
    details: Any = None
