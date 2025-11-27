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

import copy
import hashlib
import json
import os
import re
import shlex
import sys
import dataclasses
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

from absl import app, flags, logging

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.agentic_import.pipeline import (CompositeCallback, PipelineAbort,
                                           PipelineCallback, PipelineRunner,
                                           RunnerConfig, Step)
from tools.agentic_import.sdmx_pipeline_builder import build_sdmx_pipeline
from tools.agentic_import.sdmx_pipeline_config import (
    FLAG_SDMX_AGENCY,
    FLAG_SDMX_DATAFLOW_ID,
    FLAG_SDMX_DATAFLOW_KEY,
    FLAG_SDMX_DATAFLOW_PARAM,
    FLAG_SDMX_ENDPOINT,
    PipelineConfig,
    RunConfig,
    SampleConfig,
    SdmxConfig,
    SdmxDataflowConfig,
)
from tools.agentic_import.sdmx_pipeline_steps import SdmxStep
from tools.agentic_import.state_handler import StateHandler, StepState

# Flag names
_FLAG_SAMPLE_ROWS = "sample.rows"

FLAGS = flags.FLAGS


def _define_flags() -> None:
    flags.DEFINE_string(FLAG_SDMX_ENDPOINT, None, "SDMX service endpoint.")
    flags.mark_flag_as_required(FLAG_SDMX_ENDPOINT)

    flags.DEFINE_string(FLAG_SDMX_AGENCY, None,
                        "Owning SDMX agency identifier.")
    flags.mark_flag_as_required(FLAG_SDMX_AGENCY)

    flags.DEFINE_string(FLAG_SDMX_DATAFLOW_ID, None,
                        "Target SDMX dataflow identifier.")
    flags.mark_flag_as_required(FLAG_SDMX_DATAFLOW_ID)

    flags.DEFINE_string(FLAG_SDMX_DATAFLOW_KEY, None,
                        "Optional SDMX key or filter.")

    flags.DEFINE_string(
        FLAG_SDMX_DATAFLOW_PARAM, None,
        "Optional SDMX parameter appended to the dataflow query.")

    flags.DEFINE_integer(_FLAG_SAMPLE_ROWS, 1000,
                         "Number of rows to sample from downloaded data.")

    flags.DEFINE_string(
        "dataset_prefix", None,
        "Optional dataset prefix to override auto-derived values.")

    flags.DEFINE_string("run_only", None,
                        "Execute only a specific pipeline step by name.")

    flags.DEFINE_boolean("force", False, "Force all steps to run.")

    flags.DEFINE_boolean("verbose", False, "Enable verbose logging.")

    flags.DEFINE_boolean("skip_confirmation", False,
                         "Skip interactive confirmation prompts.")

    flags.DEFINE_string("gemini_cli", "gemini",
                        "Path to Gemini CLI executable.")

    flags.DEFINE_string("working_dir", None,
                        "Working directory for the pipeline.")


def _format_time(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _sanitize_run_id(dataflow: str) -> str:
    normalized = dataflow.lower()
    normalized = re.sub(r"[^a-z0-9_]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    return normalized.strip("_")


def _resolve_dataset_prefix(config: PipelineConfig) -> str:
    if config.run.dataset_prefix:
        return config.run.dataset_prefix
    if not config.sdmx.dataflow.id:
        raise ValueError(
            "dataflow.id or dataset_prefix is required to derive dataset prefix"
        )
    sanitized = _sanitize_run_id(config.sdmx.dataflow.id)
    if not sanitized:
        raise ValueError("dataflow value is invalid after sanitization")
    return sanitized


def _compute_critical_input_hash(config: PipelineConfig) -> str:
    payload = {
        FLAG_SDMX_AGENCY: config.sdmx.agency,
        FLAG_SDMX_DATAFLOW_ID: config.sdmx.dataflow.id,
        FLAG_SDMX_ENDPOINT: config.sdmx.endpoint,
        FLAG_SDMX_DATAFLOW_KEY: config.sdmx.dataflow.key,
        FLAG_SDMX_DATAFLOW_PARAM: config.sdmx.dataflow.param,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _resolve_working_dir(config: PipelineConfig) -> Path:
    directory = Path(config.run.working_dir or os.getcwd()).resolve()
    if directory.exists() and not directory.is_dir():
        raise ValueError(f"working_dir is not a directory: {directory}")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _resolve_config(config: PipelineConfig) -> PipelineConfig:
    """Resolves dynamic configuration values and returns a new config."""
    dataset_prefix = _resolve_dataset_prefix(config)
    working_dir = _resolve_working_dir(config)
    new_run = dataclasses.replace(config.run,
                                  dataset_prefix=dataset_prefix,
                                  working_dir=str(working_dir))
    return dataclasses.replace(config, run=new_run)


class InteractiveCallback(PipelineCallback):
    """Prompts the user before each step runs."""

    def before_step(self, step: Step) -> None:
        if isinstance(step, SdmxStep):
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


def run_sdmx_pipeline(
    *,
    config: PipelineConfig,
    now_fn: Callable[[], datetime] | None = None,
) -> None:
    """Orchestrates the SDMX pipeline for the provided configuration."""
    resolved_config = _resolve_config(config)
    working_dir = Path(resolved_config.run.working_dir)
    dataset_prefix = resolved_config.run.dataset_prefix
    state_handler = StateHandler(
        state_path=working_dir / ".datacommons" /
        f"{dataset_prefix}.state.json",
        dataset_prefix=dataset_prefix,
    )
    state = state_handler.get_state()
    # Snapshot state for planning so callback mutations do not affect scheduling.
    state_snapshot = copy.deepcopy(state)
    critical_hash = _compute_critical_input_hash(resolved_config)
    pipeline = build_sdmx_pipeline(config=resolved_config,
                                   state=state_snapshot,
                                   critical_input_hash=critical_hash)
    callback = build_pipeline_callback(
        state_handler=state_handler,
        dataset_prefix=dataset_prefix,
        critical_input_hash=critical_hash,
        command=resolved_config.run.command,
        skip_confirmation=resolved_config.run.skip_confirmation,
        now_fn=now_fn,
    )
    if resolved_config.run.verbose:
        logging.set_verbosity(logging.DEBUG)
    runner = PipelineRunner(RunnerConfig())
    runner.run(pipeline, callback)


def prepare_config() -> PipelineConfig:
    """Builds PipelineConfig from CLI flags."""
    # absl.flags doesn't support dots in attribute access easily,
    # so we access the flag values directly from the flag names.
    command = shlex.join(sys.argv) if sys.argv else "python"
    return PipelineConfig(
        sdmx=SdmxConfig(
            endpoint=FLAGS[FLAG_SDMX_ENDPOINT].value,
            agency=FLAGS[FLAG_SDMX_AGENCY].value,
            dataflow=SdmxDataflowConfig(
                id=FLAGS[FLAG_SDMX_DATAFLOW_ID].value,
                key=FLAGS[FLAG_SDMX_DATAFLOW_KEY].value,
                param=FLAGS[FLAG_SDMX_DATAFLOW_PARAM].value,
            ),
        ),
        sample=SampleConfig(rows=FLAGS[_FLAG_SAMPLE_ROWS].value,),
        run=RunConfig(
            command=command,
            dataset_prefix=FLAGS.dataset_prefix,
            working_dir=FLAGS.working_dir,
            run_only=FLAGS.run_only,
            force=FLAGS.force,
            verbose=FLAGS.verbose,
            skip_confirmation=FLAGS.skip_confirmation,
            gemini_cli=FLAGS.gemini_cli,
        ),
    )


def main(_: list[str]) -> int:
    config = prepare_config()
    logging.info(f"SDMX pipeline configuration: {config}")
    run_sdmx_pipeline(config=config)
    return 0


if __name__ == "__main__":
    _define_flags()
    app.run(main)
