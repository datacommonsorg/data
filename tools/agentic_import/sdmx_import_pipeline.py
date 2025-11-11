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
            message=message,
        )
        self._state.steps[step.name] = step_state
        self._state.updated_at = step_state.ended_at
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
class SdmxPipelineConfig:
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
                 config: SdmxPipelineConfig) -> None:
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


@dataclass(frozen=True)
class StepSpec:
    phase: str
    name: str
    version: int
    factory: Callable[[SdmxPipelineConfig], Step]

    @property
    def full_name(self) -> str:
        return f"{self.phase}.{self.name}"


@dataclass(frozen=True)
class PhaseSpec:
    name: str
    steps: Sequence[StepSpec]


@dataclass(frozen=True)
class SdmxPhaseRegistry:
    phases: Sequence[PhaseSpec]

    def flatten(self) -> list[StepSpec]:
        flattened: list[StepSpec] = []
        for phase in self.phases:
            flattened.extend(phase.steps)
        return flattened


class SdmxPipelineBuilder:

    def __init__(self, *, config: SdmxPipelineConfig, state: PipelineState,
                 registry: SdmxPhaseRegistry) -> None:
        self._config = config
        self._state = state
        self._registry = registry
        self._specs = registry.flatten()

    def build(self) -> Pipeline:
        planned = self._plan_steps()
        steps = [spec.factory(self._config) for spec in planned]
        logging.info("Built SDMX pipeline with %d steps", len(steps))
        return Pipeline(steps=steps)

    def _plan_steps(self) -> list[StepSpec]:
        specs = self._select_specs(self._specs, self._config.run_only)
        if not specs:
            return []
        force_all = bool(self._config.force and not self._config.run_only)
        if force_all:
            return list(specs)
        scheduled: list[StepSpec] = []
        downstream = False
        for spec in specs:
            needs_run = self._should_run(spec)
            if needs_run and not downstream:
                downstream = True
            if downstream:
                scheduled.append(spec)
        if not scheduled:
            logging.info("No steps scheduled; all steps current")
        return scheduled

    def _select_specs(self, specs: Sequence[StepSpec],
                      run_only: str | None) -> list[StepSpec]:
        if not run_only:
            return list(specs)
        if "." in run_only:
            scoped = [s for s in specs if s.full_name == run_only]
            if not scoped:
                raise ValueError(f"run_only target not found: {run_only}")
            return scoped
        scoped = [s for s in specs if s.phase == run_only]
        if not scoped:
            raise ValueError(f"run_only phase not found: {run_only}")
        return scoped

    def _should_run(self, spec: StepSpec) -> bool:
        prev = self._state.steps.get(spec.full_name)
        if prev is None:
            return True
        if prev.status != "succeeded":
            return True
        if prev.version < spec.version:
            return True
        return False


def build_sdmx_pipeline(*, config: SdmxPipelineConfig, state: PipelineState,
                        registry: SdmxPhaseRegistry) -> Pipeline:
    builder = SdmxPipelineBuilder(config=config, state=state, registry=registry)
    return builder.build()
