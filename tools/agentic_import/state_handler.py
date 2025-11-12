# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""State file helpers shared by the SDMX agentic pipeline components.

The handler centralizes JSON persistence so callers (builder, callbacks) can
operate on an in-memory `PipelineState`. This implementation assumes a single
process has exclusive ownership of the state file for the duration of a run.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from absl import logging
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class StepState:
    version: int
    status: str
    started_at: str
    ended_at: str
    duration_s: float
    started_at_ts: int | None = None
    ended_at_ts: int | None = None
    message: str | None = None


@dataclass_json
@dataclass
class PipelineState:
    run_id: str
    critical_input_hash: str
    command: str
    updated_at: str
    updated_at_ts: int | None = None
    steps: dict[str, StepState] = field(default_factory=dict)


class StateHandler:
    """Minimal state manager that owns JSON file I/O."""

    def __init__(self, state_path: str | Path, dataset_prefix: str) -> None:
        self._state_path = Path(state_path)
        self._dataset_prefix = dataset_prefix
        self._state: PipelineState | None = None

    @property
    def path(self) -> Path:
        """Returns the backing state file path."""
        return self._state_path

    def get_state(self) -> PipelineState:
        if self._state is None:
            self._state = self._load_or_init()
        return self._state

    def save_state(self) -> None:
        state = self.get_state()
        self._write_state(state)

    def _load_or_init(self) -> PipelineState:
        path = self._state_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            state = self._empty_state()
            logging.info(f"Creating new state file at {path}")
            self._write_state(state)
            return state
        try:
            with path.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
            state = PipelineState.from_dict(data)
            if not state.run_id:
                state.run_id = self._dataset_prefix
            return state
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            logging.warning(f"Failed to load state file {path}: {exc}")
            self._backup_bad_file()
            state = self._empty_state()
            self._write_state(state)
            return state

    def _write_state(self, state: PipelineState) -> None:
        directory = self._state_path.parent
        directory.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(asdict(state), indent=2, sort_keys=True) + "\n"
        tmp_path = self._state_path.with_suffix(".tmp")
        tmp_path.write_text(payload, encoding="utf-8")
        tmp_path.replace(self._state_path)

    def _empty_state(self) -> PipelineState:
        return PipelineState(
            run_id=self._dataset_prefix,
            critical_input_hash="",
            command="",
            updated_at="",
            updated_at_ts=None,
        )

    def _backup_bad_file(self) -> None:
        path = self._state_path
        if not path.exists():
            return
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        backup_name = f"{path.name}.bad.{timestamp}.bak"
        backup_path = path.with_name(backup_name)
        try:
            path.replace(backup_path)
            logging.warning(f"Backed up corrupt state to {backup_path}")
        except OSError as exc:
            logging.warning(
                f"Failed to backup corrupt state file {path}: {exc}")
