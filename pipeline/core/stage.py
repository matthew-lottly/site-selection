"""Abstract base class for every step of the site-selection pipeline."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class PipelineStage(ABC):
    """One numbered step of the pipeline.

    Subclasses declare ``id``, ``name``, and ``description`` as class
    attributes, implement :meth:`run`, and optionally list the output
    file(s) they're responsible for producing in ``outputs`` so the default
    :meth:`validate` can confirm the stage actually did its job.
    """

    id: str
    name: str
    description: str
    outputs: tuple[Path, ...] = ()

    @abstractmethod
    def run(self) -> None:
        """Execute the stage: fetch/transform/score/write, as applicable."""

    def validate(self) -> None:
        """Confirm every declared output was produced. Override to add
        stronger checks (row counts, required columns, value ranges, ...)."""
        missing = [str(p) for p in self.outputs if not p.exists()]
        if missing:
            raise RuntimeError(f"stage {self.id} ({self.name}) did not produce: {missing}")

    def __repr__(self) -> str:
        return f"<Stage {self.id} {self.name}>"
