"""Base definitions and interfaces for POI formats."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class POIRecord:
    """Represents a normalized POI point."""

    id: str
    lat: float
    lon: float
    name: str
    description: str = ""
    category: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


class POIWriter(Protocol):
    """Protocol for POI file format writers."""

    def write(self, records: Sequence[POIRecord], destination: Path) -> list[Path]:
        """Write records to destination path(s), handling chunking if necessary.

        Args:
            records: Sequence of POI records to write.
            destination: Target file or base path.

        Returns:
            List of generated file paths.
        """
        ...
