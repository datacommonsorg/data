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

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Sequence

from absl import logging

from tools.agentic_import.pipeline import (CompositeCallback, Pipeline,
                                           PipelineAbort, PipelineCallback,
                                           Step)
from tools.agentic_import.state_handler import (PipelineState, StateHandler,
                                                StepState)


def _format_time(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


class InteractiveCallback(PipelineCallback):
    """Prompts the user before each step runs."""

    def before_step(self, step: Step) -> None:
        logging.info(f"Dry run for {step.name} (v{step.version}):")
        step.dry_run()
        prompt = f"Run step {step.name} (v{step.version})? [Y/n] "
        response = input(prompt).strip().lower()
        if response in ("n", "no"):
            raise PipelineAbort("user declined interactive prompt")


class JSONStateCallback(PipelineCallback):
    """Persists pipeline progress to the SDMX state file via StateHandler.

    This callback assumes a single process owns the state file for the lifetime
    of the run. The CLI or builder sets run metadata up-front; this class only
    mutates state after a step executes.
    """

    def __init__(self,
                 *,
                 state_handler: StateHandler,
                 run_id: str,
                 critical_input_hash: str,
                 command: str,
                 now_fn: Callable[[], datetime] | None = None) -> None:
        self._handler = state_handler
        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self._state = self._handler.get_state()
        self._state.run_id = run_id
        self._state.critical_input_hash = critical_input_hash
        self._state.command = command
        self._step_start_times: dict[str, datetime] = {}
        logging.info(f"JSON state will be written to {self._handler.path}")

    def before_step(self, step: Step) -> None:
        started_at = self._now()
        self._step_start_times[step.name] = started_at

    def after_step(self, step: Step, *, error: Exception | None = None) -> None:
        ended_at = self._now()
        started_at = self._step_start_times.pop(step.name, None)
        if started_at is None:
            started_at = ended_at
        duration = max(0.0, (ended_at - started_at).total_seconds())
        started_at_ts = int(started_at.timestamp() * 1000)
        ended_at_ts = int(ended_at.timestamp() * 1000)
        if isinstance(error, PipelineAbort):
            logging.info(
                f"Skipping state update for {step.name} due to pipeline abort")
            return
        if error:
            message = str(error) or error.__class__.__name__
        else:
            message = None
        # Step stats are persisted only after the step finishes; steps can still
        # be skipped after their before_step callback runs, so we leave skipped
        # steps untouched to preserve prior state.
        step_state = StepState(
            version=step.version,
            status="failed" if error else "succeeded",
            started_at=_format_time(started_at),
            ended_at=_format_time(ended_at),
            duration_s=duration,
            started_at_ts=started_at_ts,
            ended_at_ts=ended_at_ts,
            message=message,
        )
        self._state.steps[step.name] = step_state
        self._state.updated_at = step_state.ended_at
        self._state.updated_at_ts = ended_at_ts
        self._handler.save_state()

    def _now(self) -> datetime:
        return self._now_fn()


def build_pipeline_callback(
    *,
    state_handler: StateHandler,
    run_id: str,
    critical_input_hash: str,
    command: str,
    skip_confirmation: bool,
    now_fn: Callable[[], datetime] | None = None,
) -> PipelineCallback:
    """Constructs the pipeline callback stack for the SDMX runner."""
    json_callback = JSONStateCallback(state_handler=state_handler,
                                      run_id=run_id,
                                      critical_input_hash=critical_input_hash,
                                      command=command,
                                      now_fn=now_fn)
    if skip_confirmation:
        return json_callback
    interactive = InteractiveCallback()
    return CompositeCallback([interactive, json_callback])


@dataclass(frozen=True)
class PipelineConfig:
    """User-configurable inputs that mimic planned CLI flags.

    This is a lightweight container; CLI parsing will be added in a later
    phase. Defaults are intentionally minimal.
    """

    endpoint: str | None = None
    agency: str | None = None
    dataflow: str | None = None
    key: str | None = None
    dataset_prefix: str | None = None
    working_dir: str | None = None
    run_only: str | None = None
    force: bool = False
    verbose: bool = False
    skip_confirmation: bool = False


class SdmxStep(Step):
    """Base class for SDMX steps that carries immutable config and version."""

    def __init__(self, *, name: str, version: int,
                 config: PipelineConfig) -> None:
        if not name:
            raise ValueError("step requires a name")
        self._name = name
        self._version = version
        self._config = config

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> int:
        return self._version

    # Subclasses must implement run() and dry_run().


class DownloadDataStep(SdmxStep):
    """Downloads SDMX data payloads."""

    VERSION = 1

    def __init__(self, *, name: str, config: PipelineConfig) -> None:
        super().__init__(name=name, version=self.VERSION, config=config)

    def run(self) -> None:
        logging.info(
            f"{self.name}: no-op implementation for VERSION={self.VERSION}")

    def dry_run(self) -> None:
        logging.info(f"{self.name} (dry run): previewing data download inputs")


class DownloadMetadataStep(SdmxStep):
    """Downloads SDMX metadata payloads."""

    VERSION = 1

    def __init__(self, *, name: str, config: PipelineConfig) -> None:
        super().__init__(name=name, version=self.VERSION, config=config)

    def run(self) -> None:
        logging.info(
            f"{self.name}: no-op implementation for VERSION={self.VERSION}")

    def dry_run(self) -> None:
        logging.info(
            f"{self.name} (dry run): previewing metadata download inputs")


class CreateSampleStep(SdmxStep):
    """Creates a sample dataset from downloaded data."""

    VERSION = 1

    def __init__(self, *, name: str, config: PipelineConfig) -> None:
        super().__init__(name=name, version=self.VERSION, config=config)

    def run(self) -> None:
        logging.info(
            f"{self.name}: no-op implementation for VERSION={self.VERSION}")

    def dry_run(self) -> None:
        logging.info(f"{self.name} (dry run): previewing sample generation")


class CreateSchemaMapStep(SdmxStep):
    """Builds schema mappings for transformed data."""

    VERSION = 1

    def __init__(self, *, name: str, config: PipelineConfig) -> None:
        super().__init__(name=name, version=self.VERSION, config=config)

    def run(self) -> None:
        logging.info(
            f"{self.name}: no-op implementation for VERSION={self.VERSION}")

    def dry_run(self) -> None:
        logging.info(
            f"{self.name} (dry run): previewing schema mapping outputs")


class ProcessFullDataStep(SdmxStep):
    """Processes full SDMX data into DC artifacts."""

    VERSION = 1

    def __init__(self, *, name: str, config: PipelineConfig) -> None:
        super().__init__(name=name, version=self.VERSION, config=config)

    def run(self) -> None:
        logging.info(
            f"{self.name}: no-op implementation for VERSION={self.VERSION}")

    def dry_run(self) -> None:
        logging.info(f"{self.name} (dry run): previewing full-data processing")


class CreateDcConfigStep(SdmxStep):
    """Generates Datacommons configuration artifacts."""

    VERSION = 1

    def __init__(self, *, name: str, config: PipelineConfig) -> None:
        super().__init__(name=name, version=self.VERSION, config=config)

    def run(self) -> None:
        logging.info(
            f"{self.name}: no-op implementation for VERSION={self.VERSION}")

    def dry_run(self) -> None:
        logging.info(f"{self.name} (dry run): previewing DC config creation")


class PipelineBuilder:

    def __init__(self, *, config: PipelineConfig, state: PipelineState,
                 steps: Sequence[Step]) -> None:
        self._config = config
        self._state = state
        self._steps = steps

    def build(self) -> Pipeline:
        planned = self._plan_steps()
        logging.info("Built SDMX pipeline with %d steps", len(planned))
        return Pipeline(steps=planned)

    def _plan_steps(self) -> list[Step]:
        if self._config.run_only:
            return self._filter_run_only(self._steps, self._config.run_only)
        if self._config.force:
            return list(self._steps)
        scheduled: list[Step] = []
        schedule_all_remaining = False
        previous: Step | None = None
        for step in self._steps:
            if schedule_all_remaining:
                scheduled.append(step)
            else:
                needs_run = self._should_run(step)
                if not needs_run and previous is not None:
                    needs_run = self._predecessor_newer(previous, step)
                if needs_run:
                    scheduled.append(step)
                    schedule_all_remaining = True
            previous = step
        if not scheduled:
            logging.info("No steps scheduled.")
        return scheduled

    def _filter_run_only(self, steps: Sequence[Step],
                         run_only: str) -> list[Step]:
        scoped = [s for s in steps if s.name == run_only]
        if not scoped:
            raise ValueError(f"run_only step not found: {run_only}")
        return scoped

    def _should_run(self, step: Step) -> bool:
        prev = self._state.steps.get(step.name)
        if prev is None:
            return True
        if prev.status != "succeeded":
            return True
        if prev.version < step.version:
            return True
        return False

    def _predecessor_newer(self, prev_step: Step, step: Step) -> bool:
        prev_state = self._state.steps.get(prev_step.name)
        curr_state = self._state.steps.get(step.name)
        if prev_state is None or prev_state.ended_at_ts is None:
            return False
        if curr_state is None:
            return True
        if curr_state.status != "succeeded":
            return True
        if curr_state.ended_at_ts is None:
            return True
        return prev_state.ended_at_ts > curr_state.ended_at_ts


def build_steps(config: PipelineConfig) -> list[Step]:
    """Constructs the hard-coded list of canonical steps."""
    return [
        DownloadDataStep(name="download-data", config=config),
        DownloadMetadataStep(name="download-metadata", config=config),
        CreateSampleStep(name="create-sample", config=config),
        CreateSchemaMapStep(name="create-schema-mapping", config=config),
        ProcessFullDataStep(name="process-full-data", config=config),
        CreateDcConfigStep(name="create-dc-config", config=config),
    ]


def build_sdmx_pipeline(*,
                        config: PipelineConfig,
                        state: PipelineState,
                        steps: Sequence[Step] | None = None) -> Pipeline:
    builder_steps = steps if steps is not None else build_steps(config)
    builder = PipelineBuilder(config=config, state=state, steps=builder_steps)
    return builder.build()
