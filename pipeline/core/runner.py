"""Orchestrator that runs an ordered list of PipelineStage instances."""
from __future__ import annotations

import sys
import time

from .stage import PipelineStage


class Pipeline:
    """Runs a fixed, ordered sequence of pipeline stages.

    Each stage is run() then validate()d before moving on, so a stage that
    silently failed to produce its output stops the run instead of letting
    a later stage fail on missing input with a confusing error.
    """

    def __init__(self, stages: list[PipelineStage]) -> None:
        self.stages = stages

    def _find(self, stage_id: str) -> PipelineStage:
        for stage in self.stages:
            if stage.id == stage_id:
                return stage
        raise KeyError(f"no such stage id: {stage_id!r}")

    def run_all(self, only: set[str] | None = None) -> None:
        selected = self.stages if only is None else [s for s in self.stages if s.id in only]
        if only is not None:
            missing = only - {s.id for s in selected}
            if missing:
                raise KeyError(f"no such stage id(s): {sorted(missing)}")

        for stage in selected:
            print(f"=== [{stage.id}] {stage.name} ===", file=sys.stderr)
            t0 = time.time()
            stage.run()
            stage.validate()
            print(f"    done in {time.time() - t0:.1f}s", file=sys.stderr)

    def list_stages(self) -> None:
        for stage in self.stages:
            print(f"{stage.id}  {stage.name:38s} {stage.description}")
