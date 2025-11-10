# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Helpers for the SDMX agentic import pipeline."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from absl import logging

from tools.agentic_import.pipeline import PipelineCallback, Step


def _format_time(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


@dataclass
class StepState:
    version: int
    status: str
    started_at: str
    ended_at: str
    duration_s: float
    message: str | None = None


@dataclass
class PipelineState:
    run_id: str
    critical_input_hash: str
    command: str
    updated_at: str
    steps: dict[str, StepState] = field(default_factory=dict)


class JSONStateCallback(PipelineCallback):
    """Persists pipeline progress to the SDMX state file.

    The callback is intentionally unaware of planning concerns. The CLI computes
    identifiers such as run_id and critical_input_hash before invoking the
    runner, then instantiates this callback with the desired destination file.
    """

    def __init__(self,
                 *,
                 state_path: str | Path,
                 run_id: str,
                 critical_input_hash: str,
                 command: str,
                 now_fn: Callable[[], datetime] | None = None) -> None:
        self._state_path = Path(state_path)
        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self._state = PipelineState(
            run_id=run_id,
            critical_input_hash=critical_input_hash,
            command=command,
            updated_at=_format_time(self._now()),
        )
        self._step_start_times: dict[str, datetime] = {}
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        logging.info("JSON state will be written to %s", self._state_path)

    def before_step(self, step: Step) -> None:
        started_at = self._now()
        self._step_start_times[step.name] = started_at

    def after_step(self, step: Step, *, error: Exception | None = None) -> None:
        ended_at = self._now()
        started_at = self._step_start_times.pop(step.name, None)
        if started_at is None:
            started_at = ended_at
        duration = max(0.0, (ended_at - started_at).total_seconds())
        step_state = StepState(
            version=step.version,
            status="failed" if error else "succeeded",
            started_at=_format_time(started_at),
            ended_at=_format_time(ended_at),
            duration_s=duration,
            message=str(error) or error.__class__.__name__ if error else None,
        )
        self._state.steps[step.name] = step_state
        self._state.updated_at = step_state.ended_at
        self._write_state()

    def _now(self) -> datetime:
        return self._now_fn()

    def _write_state(self) -> None:
        temp_path = self._state_path.with_suffix(self._state_path.suffix + ".tmp")
        with temp_path.open("w", encoding="utf-8") as fp:
            json.dump(asdict(self._state), fp, indent=2, sort_keys=True)
            fp.write("\n")
        temp_path.replace(self._state_path)
