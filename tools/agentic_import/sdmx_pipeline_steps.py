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
"""Step implementations for the SDMX agentic import pipeline."""

from __future__ import annotations

import abc
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Sequence

from absl import logging

from tools.agentic_import.pipeline import Step
from tools.agentic_import.sdmx_pipeline_config import (
    FLAG_SDMX_AGENCY,
    FLAG_SDMX_DATAFLOW_ID,
    FLAG_SDMX_ENDPOINT,
    PipelineConfig,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

SDMX_CLI_PATH = REPO_ROOT / "tools" / "sdmx_import" / "sdmx_cli.py"
DATA_SAMPLER_PATH = REPO_ROOT / "tools" / "statvar_importer" / "data_sampler.py"
STAT_VAR_PROCESSOR_PATH = (REPO_ROOT / "tools" / "statvar_importer" /
                           "stat_var_processor.py")
PVMAP_GENERATOR_PATH = REPO_ROOT / "tools" / "agentic_import" / "pvmap_generator.py"
SDMX_METADATA_EXTRACTOR_PATH = (REPO_ROOT / "tools" / "agentic_import" /
                                "sdmx_metadata_extractor.py")
DC_CONFIG_GENERATOR_PATH = (REPO_ROOT / "tools" / "agentic_import" /
                            "generate_custom_dc_config.py")

SAMPLE_OUTPUT_DIR = Path("sample_output")
FINAL_OUTPUT_DIR = Path("output")


def _require_config_field(value: str | None, field_name: str,
                          step_name: str) -> str:
    if value:
        return value
    raise ValueError(f"{step_name} requires config.{field_name}")


def _run_command(command: Sequence[str], *, verbose: bool) -> None:
    if verbose:
        logging.debug(f"Running command: {' '.join(command)}")
    subprocess.run(command, check=True)


class SdmxStep(Step):
    """Base class for SDMX steps that carries immutable config and version."""

    def __init__(self, *, name: str, version: str,
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
    def version(self) -> str:
        return self._version

    @abc.abstractmethod
    def dry_run(self) -> None:
        """Log a read-only preview of the work to be done."""


class DownloadDataStep(SdmxStep):
    """Downloads SDMX data payloads."""

    VERSION = "1"

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
                                         FLAG_SDMX_ENDPOINT, self.name)
        agency = _require_config_field(self._config.sdmx.agency,
                                       FLAG_SDMX_AGENCY, self.name)
        dataflow = _require_config_field(self._config.sdmx.dataflow.id,
                                         FLAG_SDMX_DATAFLOW_ID, self.name)
        dataset_prefix = self._config.run.dataset_prefix
        working_dir = Path(self._config.run.working_dir).resolve()
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

    VERSION = "1"

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
                                         FLAG_SDMX_ENDPOINT, self.name)
        agency = _require_config_field(self._config.sdmx.agency,
                                       FLAG_SDMX_AGENCY, self.name)
        dataflow = _require_config_field(self._config.sdmx.dataflow.id,
                                         FLAG_SDMX_DATAFLOW_ID, self.name)
        dataset_prefix = self._config.run.dataset_prefix
        working_dir = Path(self._config.run.working_dir).resolve()
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


class ExtractMetadataStep(SdmxStep):
    """Extracts SDMX metadata to JSON for downstream steps."""

    VERSION = "1"

    @dataclass(frozen=True)
    class _StepContext:
        input_path: Path
        output_path: Path
        full_command: list[str]

    def __init__(self, *, name: str, config: PipelineConfig) -> None:
        super().__init__(name=name, version=self.VERSION, config=config)
        self._context: ExtractMetadataStep._StepContext | None = None

    def _prepare_command(self) -> _StepContext:
        if self._context:
            return self._context
        dataset_prefix = self._config.run.dataset_prefix
        working_dir = Path(self._config.run.working_dir).resolve()
        input_path = working_dir / f"{dataset_prefix}_metadata.xml"
        output_path = working_dir / f"{dataset_prefix}_metadata.json"
        args = [
            f"--input_metadata={input_path}",
            f"--output_path={output_path}",
        ]
        full_command = [sys.executable,
                        str(SDMX_METADATA_EXTRACTOR_PATH)] + args
        self._context = ExtractMetadataStep._StepContext(
            input_path=input_path,
            output_path=output_path,
            full_command=full_command,
        )
        return self._context

    def run(self) -> None:
        context = self._prepare_command()
        if not context.input_path.is_file():
            raise RuntimeError(
                f"Metadata XML file missing: {context.input_path}")
        if self._config.run.verbose:
            logging.info(
                f"Starting SDMX metadata extraction: {' '.join(context.full_command)} -> {context.output_path}"
            )
        else:
            logging.info(
                f"Extracting SDMX metadata to {context.output_path}")
        _run_command(context.full_command, verbose=self._config.run.verbose)

    def dry_run(self) -> None:
        context = self._prepare_command()
        logging.info(
            f"{self.name} (dry run): would run {' '.join(context.full_command)}"
        )


class CreateSampleStep(SdmxStep):
    """Creates a sample dataset from downloaded data."""

    VERSION = "1"

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
        working_dir = Path(self._config.run.working_dir).resolve()
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

    VERSION = "1"

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
        working_dir = Path(self._config.run.working_dir).resolve()
        sample_path = working_dir / f"{dataset_prefix}_sample.csv"
        metadata_path = self._resolve_metadata_path(
            working_dir=working_dir, dataset_prefix=dataset_prefix)
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
        args.append(f"--working_dir={working_dir}")

        full_command = [sys.executable, str(PVMAP_GENERATOR_PATH)] + args
        self._context = CreateSchemaMapStep._StepContext(
            sample_path=sample_path,
            metadata_path=metadata_path,
            output_prefix=output_prefix,
            full_command=full_command)
        return self._context

    def _resolve_metadata_path(self, *, working_dir: Path,
                               dataset_prefix: str) -> Path:
        extracted_path = working_dir / f"{dataset_prefix}_metadata.json"
        xml_path = working_dir / f"{dataset_prefix}_metadata.xml"
        if extracted_path.is_file():
            logging.info(f"Using extracted SDMX metadata: {extracted_path}")
            return extracted_path
        logging.info(
            f"Extracted SDMX metadata not found; falling back to XML: {xml_path}"
        )
        return xml_path

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

    VERSION = "1"

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
        working_dir = Path(self._config.run.working_dir).resolve()
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

    VERSION = "1"

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
        working_dir = Path(self._config.run.working_dir).resolve()
        input_csv = working_dir / FINAL_OUTPUT_DIR / f"{dataset_prefix}.csv"
        output_config = (working_dir / FINAL_OUTPUT_DIR /
                         f"{dataset_prefix}_config.json")

        endpoint = _require_config_field(self._config.sdmx.endpoint,
                                         FLAG_SDMX_ENDPOINT, self.name)
        agency = _require_config_field(self._config.sdmx.agency,
                                       FLAG_SDMX_AGENCY, self.name)
        dataflow = _require_config_field(self._config.sdmx.dataflow.id,
                                         FLAG_SDMX_DATAFLOW_ID, self.name)

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
