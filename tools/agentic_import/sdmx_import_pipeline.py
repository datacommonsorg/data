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

import abc
import copy
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, ClassVar, Sequence

from absl import app, flags, logging

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.agentic_import.pipeline import (CompositeCallback, Pipeline,
                                           PipelineAbort, PipelineCallback,
                                           PipelineRunner, RunnerConfig, Step)
from tools.agentic_import.state_handler import (PipelineState, StateHandler,
                                                StepState)

SDMX_CLI_PATH = REPO_ROOT / "tools" / "sdmx_import" / "sdmx_cli.py"
DATA_SAMPLER_PATH = REPO_ROOT / "tools" / "statvar_importer" / "data_sampler.py"
STAT_VAR_PROCESSOR_PATH = (REPO_ROOT / "tools" / "statvar_importer" /
                           "stat_var_processor.py")
PVMAP_GENERATOR_PATH = REPO_ROOT / "tools" / "agentic_import" / "pvmap_generator.py"
DC_CONFIG_GENERATOR_PATH = (REPO_ROOT / "tools" / "agentic_import" /
                            "generate_custom_dc_config.py")

SAMPLE_OUTPUT_DIR = Path("sample_output")
FINAL_OUTPUT_DIR = Path("output")

# Flag names
_FLAG_SDMX_ENDPOINT = "sdmx.endpoint"
_FLAG_SDMX_AGENCY = "sdmx.agency"
_FLAG_SDMX_DATAFLOW_ID = "sdmx.dataflow.id"
_FLAG_SDMX_DATAFLOW_KEY = "sdmx.dataflow.key"
_FLAG_SDMX_DATAFLOW_PARAM = "sdmx.dataflow.param"
_FLAG_SAMPLE_ROWS = "sample.rows"

FLAGS = flags.FLAGS


@dataclass(frozen=True)
class SdmxDataflowConfig:
    """Configuration for SDMX dataflow."""
    id: str | None = None
    key: str | None = None
    param: str | None = None


@dataclass(frozen=True)
class SdmxConfig:
    """Configuration for SDMX data access."""
    endpoint: str | None = None
    agency: str | None = None
    dataflow: SdmxDataflowConfig = field(default_factory=SdmxDataflowConfig)


@dataclass(frozen=True)
class SampleConfig:
    """Configuration for data sampling."""
    rows: int = 1000


@dataclass(frozen=True)
class RunConfig:
    """Configuration for pipeline execution."""
    command: str
    dataset_prefix: str | None = None
    working_dir: str | None = None
    run_only: str | None = None
    force: bool = False
    verbose: bool = False
    skip_confirmation: bool = False
    gemini_cli: str | None = None


@dataclass(frozen=True)
class PipelineConfig:
    """Aggregated configuration for the pipeline."""
    sdmx: SdmxConfig = field(default_factory=SdmxConfig)
    sample: SampleConfig = field(default_factory=SampleConfig)
    run: RunConfig = field(default_factory=lambda: RunConfig(command="python"))


@dataclass(frozen=True)
class StepDecision:
    """Represents whether a step will run and why."""

    RUN: ClassVar[str] = "RUN"
    SKIP: ClassVar[str] = "SKIP"

    step_name: str
    decision: str
    reason: str


@dataclass(frozen=True)
class BuildResult:
    """Output of planning that includes the pipeline and per-step decisions."""

    pipeline: Pipeline
    decisions: list[StepDecision]


def _require_config_field(value: str | None, field: str, step_name: str) -> str:
    if value:
        return value
    raise ValueError(f"{step_name} requires config.{field}")


def _run_command(command: Sequence[str], *, verbose: bool) -> None:
    if verbose:
        logging.debug(f"Running command: {' '.join(command)}")
    subprocess.run(command, check=True)


def _run_sdmx_cli(args: Sequence[str], *, verbose: bool) -> None:
    command = [sys.executable, str(SDMX_CLI_PATH), *args]
    _run_command(command, verbose=verbose)


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
        _FLAG_SDMX_AGENCY: config.sdmx.agency,
        _FLAG_SDMX_DATAFLOW_ID: config.sdmx.dataflow.id,
        _FLAG_SDMX_ENDPOINT: config.sdmx.endpoint,
        _FLAG_SDMX_DATAFLOW_KEY: config.sdmx.dataflow.key,
        _FLAG_SDMX_DATAFLOW_PARAM: config.sdmx.dataflow.param,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _resolve_working_dir(config: PipelineConfig) -> Path:
    directory = Path(config.run.working_dir or os.getcwd())
    if directory.exists():
        if not directory.is_dir():
            raise ValueError(f"working_dir is not a directory: {directory}")
    else:
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

    @abc.abstractmethod
    def dry_run(self) -> None:
        """Log a read-only preview of the work to be done."""


class DownloadDataStep(SdmxStep):
    """Downloads SDMX data payloads."""

    VERSION = 1

    @dataclass(frozen=True)
    class _StepContext:
        full_command: list[str]
        output_path: Path

    def __init__(self, *, name: str, config: PipelineConfig) -> None:
        super().__init__(name=name, version=self.VERSION, config=config)
        self._context: DownloadDataStep._StepContext | None = None

    def _prepare_command(self) -> _StepContext:
        if self._context:
            return self._context
        endpoint = _require_config_field(self._config.sdmx.endpoint,
                                         _FLAG_SDMX_ENDPOINT, self.name)
        agency = _require_config_field(self._config.sdmx.agency,
                                       _FLAG_SDMX_AGENCY, self.name)
        dataflow = _require_config_field(self._config.sdmx.dataflow.id,
                                         _FLAG_SDMX_DATAFLOW_ID, self.name)
        dataset_prefix = self._config.run.dataset_prefix
        working_dir = Path(self._config.run.working_dir)
        output_path = working_dir / f"{dataset_prefix}_data.csv"
        args = [
            "download-data",
            f"--endpoint={endpoint}",
            f"--agency={agency}",
            f"--dataflow={dataflow}",
            f"--output_path={output_path}",
        ]
        if self._config.sdmx.dataflow.key:
            args.append(f"--key={self._config.sdmx.dataflow.key}")
        if self._config.sdmx.dataflow.param:
            args.append(f"--param={self._config.sdmx.dataflow.param}")
        if self._config.run.verbose:
            args.append("--verbose")
        full_command = [sys.executable, str(SDMX_CLI_PATH)] + args
        self._context = DownloadDataStep._StepContext(full_command=full_command,
                                                      output_path=output_path)
        return self._context

    def run(self) -> None:
        context = self._prepare_command()
        if self._config.run.verbose:
            logging.info(
                f"Starting SDMX data download: {' '.join(context.full_command)} -> {context.output_path}"
            )
        else:
            logging.info(f"Downloading SDMX data to {context.output_path}")
        _run_command(context.full_command, verbose=self._config.run.verbose)

    def dry_run(self) -> None:
        context = self._prepare_command()
        logging.info(
            f"{self.name} (dry run): would run {' '.join(context.full_command)}"
        )


class DownloadMetadataStep(SdmxStep):
    """Downloads SDMX metadata payloads."""

    VERSION = 1

    @dataclass(frozen=True)
    class _StepContext:
        full_command: list[str]
        output_path: Path

    def __init__(self, *, name: str, config: PipelineConfig) -> None:
        super().__init__(name=name, version=self.VERSION, config=config)
        self._context: DownloadMetadataStep._StepContext | None = None

    def _prepare_command(self) -> _StepContext:
        if self._context:
            return self._context
        endpoint = _require_config_field(self._config.sdmx.endpoint,
                                         _FLAG_SDMX_ENDPOINT, self.name)
        agency = _require_config_field(self._config.sdmx.agency,
                                       _FLAG_SDMX_AGENCY, self.name)
        dataflow = _require_config_field(self._config.sdmx.dataflow.id,
                                         _FLAG_SDMX_DATAFLOW_ID, self.name)
        dataset_prefix = self._config.run.dataset_prefix
        working_dir = Path(self._config.run.working_dir)
        output_path = working_dir / f"{dataset_prefix}_metadata.xml"
        args = [
            "download-metadata",
            f"--endpoint={endpoint}",
            f"--agency={agency}",
            f"--dataflow={dataflow}",
            f"--output_path={output_path}",
        ]
        if self._config.run.verbose:
            args.append("--verbose")
        full_command = [sys.executable, str(SDMX_CLI_PATH)] + args
        self._context = DownloadMetadataStep._StepContext(
            full_command=full_command, output_path=output_path)
        return self._context

    def run(self) -> None:
        context = self._prepare_command()
        if self._config.run.verbose:
            logging.info(
                f"Starting SDMX metadata download: {' '.join(context.full_command)} -> {context.output_path}"
            )
        else:
            logging.info(f"Downloading SDMX metadata to {context.output_path}")
        _run_command(context.full_command, verbose=self._config.run.verbose)

    def dry_run(self) -> None:
        context = self._prepare_command()
        logging.info(
            f"{self.name} (dry run): would run {' '.join(context.full_command)}"
        )


class CreateSampleStep(SdmxStep):
    """Creates a sample dataset from downloaded data."""

    VERSION = 1

    @dataclass(frozen=True)
    class _StepContext:
        input_path: Path
        full_command: list[str]
        output_path: Path

    def __init__(self, *, name: str, config: PipelineConfig) -> None:
        super().__init__(name=name, version=self.VERSION, config=config)
        self._context: CreateSampleStep._StepContext | None = None

    def _prepare_command(self) -> _StepContext:
        if self._context:
            return self._context
        dataset_prefix = self._config.run.dataset_prefix
        working_dir = Path(self._config.run.working_dir)
        input_path = working_dir / f"{dataset_prefix}_data.csv"
        output_path = working_dir / f"{dataset_prefix}_sample.csv"

        args = [
            f"--sampler_input={input_path}",
            f"--sampler_output={output_path}",
            f"--sampler_output_rows={self._config.sample.rows}",
        ]
        full_command = [sys.executable, str(DATA_SAMPLER_PATH)] + args
        self._context = CreateSampleStep._StepContext(input_path=input_path,
                                                      full_command=full_command,
                                                      output_path=output_path)
        return self._context

    def run(self) -> None:
        context = self._prepare_command()
        if not context.input_path.is_file():
            raise RuntimeError(
                f"Input file missing for sampling: {context.input_path}")
        if self._config.run.verbose:
            logging.info(
                f"Starting data sampling: {' '.join(context.full_command)} -> {context.output_path}"
            )
        else:
            logging.info(f"Sampling data to {context.output_path}")
        _run_command(context.full_command, verbose=self._config.run.verbose)

    def dry_run(self) -> None:
        context = self._prepare_command()
        logging.info(
            f"{self.name} (dry run): would run {' '.join(context.full_command)}"
        )


class CreateSchemaMapStep(SdmxStep):
    """Builds schema mappings for transformed data."""

    VERSION = 1

    @dataclass(frozen=True)
    class _StepContext:
        sample_path: Path
        metadata_path: Path
        output_prefix: Path
        full_command: list[str]

    def __init__(self, *, name: str, config: PipelineConfig) -> None:
        super().__init__(name=name, version=self.VERSION, config=config)
        self._context: CreateSchemaMapStep._StepContext | None = None

    def _prepare_command(self) -> _StepContext:
        if self._context:
            return self._context
        dataset_prefix = self._config.run.dataset_prefix
        working_dir = Path(self._config.run.working_dir)
        sample_path = working_dir / f"{dataset_prefix}_sample.csv"
        metadata_path = working_dir / f"{dataset_prefix}_metadata.xml"
        output_prefix = working_dir / SAMPLE_OUTPUT_DIR / dataset_prefix

        args = [
            f"--input_data={sample_path}",
            f"--input_metadata={metadata_path}",
            "--sdmx_dataset",
            f"--output_path={output_prefix}",
        ]
        if self._config.run.skip_confirmation:
            args.append("--skip_confirmation")
        if self._config.run.gemini_cli:
            args.append(f"--gemini_cli={self._config.run.gemini_cli}")

        full_command = [sys.executable, str(PVMAP_GENERATOR_PATH)] + args
        self._context = CreateSchemaMapStep._StepContext(
            sample_path=sample_path,
            metadata_path=metadata_path,
            output_prefix=output_prefix,
            full_command=full_command)
        return self._context

    def run(self) -> None:
        context = self._prepare_command()
        if not context.sample_path.is_file():
            raise RuntimeError(f"Sample file missing: {context.sample_path}")
        if not context.metadata_path.is_file():
            raise RuntimeError(
                f"Metadata file missing: {context.metadata_path}")
        context.output_prefix.parent.mkdir(parents=True, exist_ok=True)
        logging.info(
            f"Starting PV map generation: {' '.join(context.full_command)} -> {context.output_prefix}"
        )
        _run_command(context.full_command, verbose=self._config.run.verbose)

    def dry_run(self) -> None:
        context = self._prepare_command()
        logging.info(
            f"{self.name} (dry run): would run {' '.join(context.full_command)}"
        )


class ProcessFullDataStep(SdmxStep):
    """Processes full SDMX data into DC artifacts."""

    VERSION = 1

    RUN_OUTPUT_COLUMNS: ClassVar[str] = (
        "observationDate,observationAbout,variableMeasured,value,"
        "observationPeriod,measurementMethod,unit,scalingFactor")

    @dataclass(frozen=True)
    class _StepContext:
        input_data_path: Path
        pv_map_path: Path
        metadata_path: Path
        full_command: list[str]
        output_prefix: Path

    def __init__(self, *, name: str, config: PipelineConfig) -> None:
        super().__init__(name=name, version=self.VERSION, config=config)
        self._context: ProcessFullDataStep._StepContext | None = None

    def _prepare_command(self) -> _StepContext:
        if self._context:
            return self._context
        dataset_prefix = self._config.run.dataset_prefix
        working_dir = Path(self._config.run.working_dir)
        input_data_path = working_dir / f"{dataset_prefix}_data.csv"
        pv_map_path = (working_dir / SAMPLE_OUTPUT_DIR /
                       f"{dataset_prefix}_pvmap.csv")
        metadata_path = (working_dir / SAMPLE_OUTPUT_DIR /
                         f"{dataset_prefix}_metadata.csv")
        output_prefix = working_dir / FINAL_OUTPUT_DIR / dataset_prefix

        args = [
            f"--input_data={input_data_path}",
            f"--pv_map={pv_map_path}",
            f"--config_file={metadata_path}",
            "--generate_statvar_name=True",
            "--skip_constant_csv_columns=False",
            f"--output_columns={self.RUN_OUTPUT_COLUMNS}",
            f"--output_path={output_prefix}",
        ]
        full_command = [sys.executable, str(STAT_VAR_PROCESSOR_PATH)] + args
        self._context = ProcessFullDataStep._StepContext(
            input_data_path=input_data_path,
            pv_map_path=pv_map_path,
            metadata_path=metadata_path,
            full_command=full_command,
            output_prefix=output_prefix,
        )
        return self._context

    def run(self) -> None:
        context = self._prepare_command()
        for required in (context.input_data_path, context.pv_map_path,
                         context.metadata_path):
            if not required.is_file():
                raise RuntimeError(
                    f"{self.name} requires existing input: {required}")
        # Ensure output directory exists
        context.output_prefix.parent.mkdir(parents=True, exist_ok=True)
        logging.info(
            f"Starting stat_var_processor: input={context.input_data_path} "
            f"pvmap={context.pv_map_path} metadata={context.metadata_path} -> "
            f"{context.output_prefix}")
        _run_command(context.full_command, verbose=self._config.run.verbose)

    def dry_run(self) -> None:
        context = self._prepare_command()
        logging.info(
            f"{self.name} (dry run): would run {' '.join(context.full_command)}"
        )


class CreateDcConfigStep(SdmxStep):
    """Generates Datacommons configuration artifacts."""

    VERSION = 1

    @dataclass(frozen=True)
    class _StepContext:
        input_csv: Path
        output_config: Path
        full_command: list[str]

    def __init__(self, *, name: str, config: PipelineConfig) -> None:
        super().__init__(name=name, version=self.VERSION, config=config)
        self._context: CreateDcConfigStep._StepContext | None = None

    def _prepare_command(self) -> _StepContext:
        if self._context:
            return self._context
        dataset_prefix = self._config.run.dataset_prefix
        working_dir = Path(self._config.run.working_dir)
        input_csv = working_dir / FINAL_OUTPUT_DIR / f"{dataset_prefix}.csv"
        output_config = (working_dir / FINAL_OUTPUT_DIR /
                         f"{dataset_prefix}_config.json")

        endpoint = _require_config_field(self._config.sdmx.endpoint,
                                         _FLAG_SDMX_ENDPOINT, self.name)
        agency = _require_config_field(self._config.sdmx.agency,
                                       _FLAG_SDMX_AGENCY, self.name)
        dataflow = _require_config_field(self._config.sdmx.dataflow.id,
                                         _FLAG_SDMX_DATAFLOW_ID, self.name)

        dataset_url = (f"{endpoint.rstrip('/')}/data/"
                       f"{agency},{dataflow},")

        args = [
            f"--input_csv={input_csv}",
            f"--output_config={output_config}",
            f"--provenance_name={dataflow}",
            f"--source_name={agency}",
            f"--data_source_url={endpoint}",
            f"--dataset_url={dataset_url}",
        ]
        full_command = [sys.executable, str(DC_CONFIG_GENERATOR_PATH)] + args
        self._context = CreateDcConfigStep._StepContext(
            input_csv=input_csv,
            output_config=output_config,
            full_command=full_command)
        return self._context

    def run(self) -> None:
        context = self._prepare_command()
        if not context.input_csv.is_file():
            raise RuntimeError(
                f"{self.name} requires existing input: {context.input_csv}")

        logging.info(
            f"Starting custom DC config generation: input={context.input_csv} -> {context.output_config}"
        )
        _run_command(context.full_command, verbose=self._config.run.verbose)

    def dry_run(self) -> None:
        context = self._prepare_command()
        logging.info(
            f"{self.name} (dry run): would run {' '.join(context.full_command)}"
        )


class PipelineBuilder:

    def __init__(self,
                 *,
                 config: PipelineConfig,
                 state: PipelineState,
                 steps: Sequence[Step],
                 critical_input_hash: str | None = None) -> None:
        self._config = config
        self._state = state
        self._steps = steps
        self._critical_input_hash = critical_input_hash

    def build(self) -> BuildResult:
        if self._config.run.run_only:
            planned, decisions = self._plan_run_only(self._config.run.run_only)
        elif self._config.run.force:
            logging.info("Force flag set; scheduling all SDMX steps")
            planned, decisions = self._plan_all_steps(
                "Force flag set; scheduling this step")
        elif self._hash_changed():
            logging.info("Critical inputs changed; scheduling all SDMX steps")
            planned, decisions = self._plan_all_steps(
                "Critical inputs changed; scheduling this step")
        else:
            planned, decisions = self._plan_incremental()
        logging.info("Built SDMX pipeline with %d steps", len(planned))
        return BuildResult(pipeline=Pipeline(steps=planned),
                           decisions=decisions)

    def _plan_run_only(self,
                       run_only: str) -> tuple[list[Step], list[StepDecision]]:
        planned: list[Step] = []
        decisions: list[StepDecision] = []
        for step in self._steps:
            if step.name == run_only:
                planned.append(step)
                decisions.append(
                    StepDecision(
                        step_name=step.name,
                        decision=StepDecision.RUN,
                        reason=(f"run_only={run_only} requested; running only "
                                "this step"),
                    ))
            else:
                decisions.append(
                    StepDecision(
                        step_name=step.name,
                        decision=StepDecision.SKIP,
                        reason=(f"run_only={run_only} requested; skipping "
                                "this step"),
                    ))
        if not planned:
            raise ValueError(f"run_only step not found: {run_only}")
        return planned, decisions

    def _plan_all_steps(self,
                        reason: str) -> tuple[list[Step], list[StepDecision]]:
        planned: list[Step] = []
        decisions: list[StepDecision] = []
        for step in self._steps:
            planned.append(step)
            decisions.append(
                StepDecision(step_name=step.name,
                             decision=StepDecision.RUN,
                             reason=reason))
        return planned, decisions

    def _plan_incremental(self) -> tuple[list[Step], list[StepDecision]]:
        planned: list[Step] = []
        decisions: list[StepDecision] = []
        schedule_all_remaining = False
        previous: Step | None = None
        for step in self._steps:
            if schedule_all_remaining:
                planned.append(step)
                decisions.append(
                    StepDecision(
                        step_name=step.name,
                        decision=StepDecision.RUN,
                        reason=("Upstream step triggered rerun for remaining "
                                "steps"),
                    ))
                previous = step
                continue

            prev_state = self._state.steps.get(step.name)
            if prev_state is None:
                needs_run = True
                reason = "No previous state recorded; scheduling step"
            elif prev_state.status != "succeeded":
                needs_run = True
                reason = (f"Previous run status was {prev_state.status}; "
                          "rerunning step")
            elif prev_state.version < step.version:
                needs_run = True
                reason = (
                    f"Step version increased from {prev_state.version} to "
                    f"{step.version}; rerunning step")
            else:
                needs_run = False
                reason = ("Previous run succeeded with same version; step is "
                          "up-to-date")

            if not needs_run and previous is not None:
                if self._predecessor_newer(previous, step):
                    needs_run = True
                    reason = (f"Previous step {previous.name} finished more "
                              "recently; rerunning downstream steps")

            if needs_run:
                planned.append(step)
                decisions.append(
                    StepDecision(step_name=step.name,
                                 decision=StepDecision.RUN,
                                 reason=reason))
                schedule_all_remaining = True
            else:
                decisions.append(
                    StepDecision(step_name=step.name,
                                 decision=StepDecision.SKIP,
                                 reason=reason))
            previous = step

        if not planned:
            logging.info("No steps scheduled.")
        return planned, decisions

    def _hash_changed(self) -> bool:
        if not self._critical_input_hash:
            return False
        previous = self._state.critical_input_hash
        if not previous:
            return True
        return previous != self._critical_input_hash

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


def _log_step_decisions(decisions: Sequence[StepDecision]) -> None:
    for decision in decisions:
        logging.info("step=%s decision=%s reason=%s", decision.step_name,
                     decision.decision, decision.reason)


def build_sdmx_pipeline(*,
                        config: PipelineConfig,
                        state: PipelineState,
                        steps: Sequence[Step] | None = None,
                        critical_input_hash: str | None = None) -> Pipeline:
    builder_steps = steps if steps is not None else build_steps(config)
    builder = PipelineBuilder(config=config,
                              state=state,
                              steps=builder_steps,
                              critical_input_hash=critical_input_hash)
    result = builder.build()
    _log_step_decisions(result.decisions)
    return result.pipeline


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
            endpoint=FLAGS[_FLAG_SDMX_ENDPOINT].value,
            agency=FLAGS[_FLAG_SDMX_AGENCY].value,
            dataflow=SdmxDataflowConfig(
                id=FLAGS[_FLAG_SDMX_DATAFLOW_ID].value,
                key=FLAGS[_FLAG_SDMX_DATAFLOW_KEY].value,
                param=FLAGS[_FLAG_SDMX_DATAFLOW_PARAM].value,
            ),
        ),
        sample=SampleConfig(rows=FLAGS[_FLAG_SAMPLE_ROWS].value,),
        run=RunConfig(
            command=command,
            dataset_prefix=FLAGS.dataset_prefix,
            working_dir=None,
            run_only=FLAGS.run_only,
            force=FLAGS.force,
            verbose=FLAGS.verbose,
            skip_confirmation=FLAGS.skip_confirmation,
            gemini_cli=FLAGS.gemini_cli,
        ),
    )


def _define_flags() -> None:
    flags.DEFINE_string(_FLAG_SDMX_ENDPOINT, None, "SDMX service endpoint.")
    flags.mark_flag_as_required(_FLAG_SDMX_ENDPOINT)

    flags.DEFINE_string(_FLAG_SDMX_AGENCY, None,
                        "Owning SDMX agency identifier.")
    flags.mark_flag_as_required(_FLAG_SDMX_AGENCY)

    flags.DEFINE_string(_FLAG_SDMX_DATAFLOW_ID, None,
                        "Target SDMX dataflow identifier.")
    flags.mark_flag_as_required(_FLAG_SDMX_DATAFLOW_ID)

    flags.DEFINE_string(_FLAG_SDMX_DATAFLOW_KEY, None,
                        "Optional SDMX key or filter.")

    flags.DEFINE_string(
        _FLAG_SDMX_DATAFLOW_PARAM, None,
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


def main(_: list[str]) -> int:
    config = prepare_config()
    logging.info(f"SDMX pipeline configuration: {config}")
    run_sdmx_pipeline(config=config)
    return 0


if __name__ == "__main__":
    _define_flags()
    app.run(main)
