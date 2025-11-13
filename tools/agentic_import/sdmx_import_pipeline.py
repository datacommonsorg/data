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

import hashlib
import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

from absl import app, flags, logging

from tools.agentic_import.pipeline import (CompositeCallback, Pipeline,
                                           PipelineAbort, PipelineCallback,
                                           PipelineRunner, RunnerConfig, Step)
from tools.agentic_import.state_handler import (PipelineState, StateHandler,
                                                StepState)

FLAGS = flags.FLAGS


def _define_flags() -> None:
    flags.DEFINE_string("endpoint", None, "SDMX service endpoint.")
    flags.mark_flag_as_required("endpoint")

    flags.DEFINE_string("agency", None, "Owning SDMX agency identifier.")
    flags.mark_flag_as_required("agency")

    flags.DEFINE_string("dataflow", None, "Target SDMX dataflow identifier.")
    flags.mark_flag_as_required("dataflow")

    flags.DEFINE_string("dataflow_key", None, "Optional SDMX key or filter.")
    flags.DEFINE_alias("key", "dataflow_key")

    flags.DEFINE_string(
        "dataflow_param", None,
        "Optional SDMX parameter appended to the dataflow query.")

    flags.DEFINE_string(
        "dataset_prefix", None,
        "Optional dataset prefix to override auto-derived values.")

    flags.DEFINE_string("run_only", None,
                        "Execute only a specific pipeline step by name.")

    flags.DEFINE_boolean("force", False, "Force all steps to run.")

    flags.DEFINE_boolean("verbose", False, "Enable verbose logging.")

    flags.DEFINE_boolean("skip_confirmation", False,
                         "Skip interactive confirmation prompts.")


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
                 dataset_prefix: str,
                 critical_input_hash: str,
                 command: str,
                 now_fn: Callable[[], datetime] | None = None) -> None:
        self._handler = state_handler
        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        self._state = self._handler.get_state()
        self._state.dataset_prefix = dataset_prefix
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
    dataset_prefix: str,
    critical_input_hash: str,
    command: str,
    skip_confirmation: bool,
    now_fn: Callable[[], datetime] | None = None,
) -> PipelineCallback:
    """Constructs the pipeline callback stack for the SDMX runner."""
    json_callback = JSONStateCallback(state_handler=state_handler,
                                      dataset_prefix=dataset_prefix,
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

    command: str
    endpoint: str | None = None
    agency: str | None = None
    dataflow: str | None = None
    dataflow_key: str | None = None
    dataflow_param: str | None = None
    dataset_prefix: str | None = None
    working_dir: str | None = None  # TODO: Add CLI flag once semantics stabilize.
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


def _sanitize_run_id(dataflow: str) -> str:
    normalized = dataflow.lower()
    normalized = re.sub(r"[^a-z0-9_]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    return normalized.strip("_")


def _resolve_dataset_prefix(config: PipelineConfig) -> str:
    if config.dataset_prefix:
        return config.dataset_prefix
    if not config.dataflow:
        raise ValueError(
            "dataflow or dataset_prefix is required to derive dataset prefix")
    sanitized = _sanitize_run_id(config.dataflow)
    if not sanitized:
        raise ValueError("dataflow value is invalid after sanitization")
    return sanitized


def _compute_critical_input_hash(config: PipelineConfig) -> str:
    payload = {
        "agency": config.agency,
        "dataflow": config.dataflow,
        "endpoint": config.endpoint,
        "dataflow_key": config.dataflow_key,
        "dataflow_param": config.dataflow_param,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _resolve_working_dir(config: PipelineConfig) -> Path:
    directory = Path(config.working_dir or os.getcwd())
    if directory.exists():
        if not directory.is_dir():
            raise ValueError(f"working_dir is not a directory: {directory}")
    else:
        directory.mkdir(parents=True, exist_ok=True)
    return directory


def run_sdmx_pipeline(
    *,
    config: PipelineConfig,
    now_fn: Callable[[], datetime] | None = None,
) -> None:
    """Orchestrates the SDMX pipeline for the provided configuration."""
    working_dir = _resolve_working_dir(config)
    dataset_prefix = _resolve_dataset_prefix(config)
    state_handler = StateHandler(
        state_path=working_dir / ".datacommons" /
        f"{dataset_prefix}.state.json",
        dataset_prefix=dataset_prefix,
    )
    state = state_handler.get_state()
    critical_hash = _compute_critical_input_hash(config)
    state.dataset_prefix = dataset_prefix
    state.command = config.command
    state.critical_input_hash = critical_hash
    state_handler.save_state()
    pipeline = build_sdmx_pipeline(config=config, state=state)
    callback = build_pipeline_callback(
        state_handler=state_handler,
        dataset_prefix=dataset_prefix,
        critical_input_hash=critical_hash,
        command=config.command,
        skip_confirmation=config.skip_confirmation,
        now_fn=now_fn,
    )
    if config.verbose:
        logging.set_verbosity(logging.DEBUG)
    runner = PipelineRunner(RunnerConfig())
    runner.run(pipeline, callback)


def prepare_config() -> PipelineConfig:
    """Builds PipelineConfig from CLI flags."""
    command = shlex.join(sys.argv) if sys.argv else "python"
    return PipelineConfig(
        command=command,
        endpoint=FLAGS.endpoint,
        agency=FLAGS.agency,
        dataflow=FLAGS.dataflow,
        dataflow_key=FLAGS.dataflow_key,
        dataflow_param=FLAGS.dataflow_param,
        dataset_prefix=FLAGS.dataset_prefix,
        working_dir=None,
        run_only=FLAGS.run_only,
        force=FLAGS.force,
        verbose=FLAGS.verbose,
        skip_confirmation=FLAGS.skip_confirmation,
    )


def main(_: list[str]) -> int:
    config = prepare_config()
    logging.info(f"SDMX pipeline configuration: {config}")
    run_sdmx_pipeline(config=config)
    return 0


if __name__ == "__main__":
    _define_flags()
    app.run(main)
