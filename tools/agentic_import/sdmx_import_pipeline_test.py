#!/usr/bin/env python3

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
"""Unit tests for SDMX pipeline helpers."""

from __future__ import annotations

import hashlib
import dataclasses
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
_PROJECT_ROOT = os.path.dirname(_REPO_ROOT)
for path in (_PROJECT_ROOT,):
    if path not in sys.path:
        sys.path.append(path)

_TEST_COMMAND = "sdmx pipeline test"

from tools.agentic_import.pipeline import (  # pylint: disable=import-error
    BaseStep, CompositeCallback, Pipeline, PipelineAbort, PipelineRunner,
    RunnerConfig,
)
from tools.agentic_import.sdmx_import_pipeline import (  # pylint: disable=import-error
    InteractiveCallback, JSONStateCallback, PipelineBuilder, PipelineConfig,
    StepDecision, build_pipeline_callback, build_sdmx_pipeline, build_steps,
    run_sdmx_pipeline, DownloadMetadataStep, DownloadDataStep, CreateSampleStep,
    CreateSchemaMapStep, ProcessFullDataStep, CreateDcConfigStep, _run_command,
    SdmxConfig, SampleConfig, RunConfig, SdmxDataflowConfig, SdmxStep)
from tools.agentic_import.state_handler import (  # pylint: disable=import-error
    PipelineState, StateHandler, StepState)

_TEST_CONFIG = PipelineConfig(run=RunConfig(command="test"))


class _IncrementingClock:

    def __init__(self, start: datetime, step: timedelta) -> None:
        self._value = start
        self._step = step
        self._first_call = True

    def __call__(self) -> datetime:
        if self._first_call:
            self._first_call = False
            return self._value
        self._value = self._value + self._step
        return self._value


class _RecordingStep(SdmxStep):

    def __init__(self, name: str, *, should_fail: bool = False) -> None:
        super().__init__(name=name, version=1, config=_TEST_CONFIG)
        self._should_fail = should_fail

    def run(self) -> None:
        if self._should_fail:
            raise ValueError("boom")

    def dry_run(self) -> None:
        logging.info("noop")


class _VersionedStep(SdmxStep):

    def __init__(self, name: str, version: int) -> None:
        super().__init__(name=name, version=version, config=_TEST_CONFIG)

    def run(self) -> None:
        logging.info("noop")

    def dry_run(self) -> None:
        logging.info("noop")


class JSONStateCallbackTest(unittest.TestCase):

    def _build_callback(
            self, *, tmpdir: str, clock: _IncrementingClock
    ) -> tuple[JSONStateCallback, StateHandler]:
        state_path = os.path.join(tmpdir, ".datacommons", "demo.state.json")
        handler = StateHandler(state_path=state_path, dataset_prefix="demo")
        callback = JSONStateCallback(
            state_handler=handler,
            dataset_prefix="demo",
            critical_input_hash="abc123",
            command="python run",
            now_fn=clock,
        )
        return callback, handler

    def test_successful_step_persists_expected_schema(self) -> None:
        clock = _IncrementingClock(
            datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc),
            timedelta(seconds=5))
        with tempfile.TemporaryDirectory() as tmpdir:
            callback, handler = self._build_callback(tmpdir=tmpdir, clock=clock)
            pipeline = Pipeline(
                steps=[_RecordingStep("download.download-data")])
            runner = PipelineRunner(RunnerConfig())
            runner.run(pipeline, callback)

            with open(handler.path, encoding="utf-8") as fp:
                state = json.load(fp)

        step_state = state["steps"]["download.download-data"]
        self.assertEqual(state["dataset_prefix"], "demo")
        self.assertEqual(state["critical_input_hash"], "abc123")
        self.assertEqual(step_state["status"], "succeeded")
        self.assertIn("started_at", step_state)
        self.assertIn("ended_at", step_state)
        self.assertAlmostEqual(step_state["duration_s"], 5.0)
        self.assertIn("message", step_state)
        self.assertIsNone(step_state["message"])
        self.assertEqual(state["updated_at"], step_state["ended_at"])
        ended_at_dt = datetime.fromisoformat(step_state["ended_at"])
        started_at_dt = datetime.fromisoformat(step_state["started_at"])
        self.assertEqual(step_state["ended_at_ts"],
                         int(ended_at_dt.timestamp() * 1000))
        self.assertEqual(step_state["started_at_ts"],
                         int(started_at_dt.timestamp() * 1000))
        self.assertEqual(state["updated_at_ts"], step_state["ended_at_ts"])

    def test_failed_step_records_error_and_persists_file(self) -> None:
        clock = _IncrementingClock(
            datetime(2025, 1, 2, 0, 0, tzinfo=timezone.utc),
            timedelta(seconds=7))
        with tempfile.TemporaryDirectory() as tmpdir:
            callback, handler = self._build_callback(tmpdir=tmpdir, clock=clock)
            pipeline = Pipeline(steps=[
                _RecordingStep("sample.create-sample", should_fail=True)
            ])
            runner = PipelineRunner(RunnerConfig())

            with self.assertRaisesRegex(ValueError, "boom"):
                runner.run(pipeline, callback)

            with open(handler.path, encoding="utf-8") as fp:
                state = json.load(fp)

        step_state = state["steps"]["sample.create-sample"]
        self.assertEqual(step_state["status"], "failed")
        self.assertIn("boom", step_state["message"])
        self.assertAlmostEqual(step_state["duration_s"], 7.0)
        self.assertIn("ended_at_ts", step_state)
        self.assertIn("started_at_ts", step_state)

    def test_abort_skips_state_persistence(self) -> None:
        clock = _IncrementingClock(
            datetime(2025, 1, 3, 0, 0, tzinfo=timezone.utc),
            timedelta(seconds=3))
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = os.path.join(tmpdir, ".datacommons")
            os.makedirs(state_dir, exist_ok=True)
            state_path = os.path.join(state_dir, "demo.state.json")
            previous = {
                "dataset_prefix": "previous",
                "critical_input_hash": "old",
                "command": "old command",
                "updated_at": "2025-01-01T00:00:00Z",
                "updated_at_ts": 1,
                "steps": {
                    "existing.step": {
                        "version": 1,
                        "status": "succeeded",
                        "started_at": "2025-01-01T00:00:00Z",
                        "started_at_ts": 0,
                        "ended_at": "2025-01-01T00:05:00Z",
                        "ended_at_ts": 300000,
                        "duration_s": 300.0,
                        "message": None,
                    }
                },
            }
            with open(state_path, "w", encoding="utf-8") as fp:
                json.dump(previous, fp)
            callback, handler = self._build_callback(tmpdir=tmpdir, clock=clock)

            class _AbortStep(SdmxStep):

                def __init__(self) -> None:
                    super().__init__(name="download.download-data",
                                     version=1,
                                     config=_TEST_CONFIG)

                def run(self) -> None:
                    raise PipelineAbort("user requested stop")

                def dry_run(self) -> None:
                    logging.info("noop")

            pipeline = Pipeline(steps=[_AbortStep()])
            runner = PipelineRunner(RunnerConfig())
            runner.run(pipeline, callback)

            with open(handler.path, encoding="utf-8") as fp:
                state = json.load(fp)

        self.assertEqual(state, previous)


class InteractiveCallbackTest(unittest.TestCase):

    def test_prompt_accepts_and_runs_step(self) -> None:
        callback = InteractiveCallback()
        pipeline = Pipeline(steps=[_RecordingStep("download.preview")])
        runner = PipelineRunner(RunnerConfig())

        with mock.patch("builtins.input", return_value="y"):
            with self.assertLogs(logging.get_absl_logger(),
                                 level="INFO") as logs:
                runner.run(pipeline, callback)

        self.assertTrue(
            any("Dry run for download.preview" in entry
                for entry in logs.output))

    def test_prompt_decline_aborts_pipeline(self) -> None:
        events: list[str] = []

        class _TrackingStep(_RecordingStep):

            def __init__(self) -> None:
                super().__init__("sample.interactive")
                self.executed = False

            def run(self) -> None:
                self.executed = True
                super().run()

            def dry_run(self) -> None:
                events.append("dry_run")
                logging.info("noop")

        callback = InteractiveCallback()
        step = _TrackingStep()
        pipeline = Pipeline(steps=[step])
        runner = PipelineRunner(RunnerConfig())

        with mock.patch("builtins.input", return_value="n"):
            with self.assertLogs(logging.get_absl_logger(), level="INFO"):
                runner.run(pipeline, callback)

        self.assertFalse(step.executed)
        self.assertTrue(events)


class CallbackFactoryTest(unittest.TestCase):

    def _state_handler_for_tmpdir(self, tmpdir: str) -> StateHandler:
        path = os.path.join(tmpdir, ".datacommons", "demo.state.json")
        return StateHandler(state_path=path, dataset_prefix="demo")

    def test_skip_confirmation_returns_json_callback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            handler = self._state_handler_for_tmpdir(tmpdir)
            callback = build_pipeline_callback(
                state_handler=handler,
                dataset_prefix="demo",
                critical_input_hash="abc",
                command="python run",
                skip_confirmation=True,
            )
        self.assertIsInstance(callback, JSONStateCallback)

    def test_interactive_mode_returns_composite(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            handler = self._state_handler_for_tmpdir(tmpdir)
            with mock.patch("builtins.input", return_value="y"):
                callback = build_pipeline_callback(
                    state_handler=handler,
                    dataset_prefix="demo",
                    critical_input_hash="abc",
                    command="python run",
                    skip_confirmation=False,
                )
        self.assertIsInstance(callback, CompositeCallback)


class PlanningTest(unittest.TestCase):

    def _empty_state(self) -> PipelineState:
        return PipelineState(dataset_prefix="demo",
                             critical_input_hash="",
                             command="",
                             updated_at="",
                             steps={})

    def _state_with(
            self, versions: dict[str, tuple[int, str,
                                            int | None]]) -> PipelineState:
        steps = {
            name:
                StepState(version=v,
                          status=st,
                          started_at="t",
                          ended_at="t",
                          duration_s=0.0,
                          started_at_ts=ts,
                          ended_at_ts=ts,
                          message=None)
            for name, (v, st, ts) in versions.items()
        }
        return PipelineState(dataset_prefix="demo",
                             critical_input_hash="",
                             command="",
                             updated_at="",
                             updated_at_ts=None,
                             steps=steps)

    def _names_from_builder(self,
                            cfg: PipelineConfig,
                            steps: list[BaseStep] | None = None,
                            state: PipelineState | None = None) -> list[str]:
        builder_steps = steps or build_steps(cfg)
        builder = PipelineBuilder(config=cfg,
                                  state=state or self._empty_state(),
                                  steps=builder_steps)
        result = builder.build()
        pipeline = result.pipeline
        return [step.name for step in pipeline.get_steps()]

    def test_run_only_step(self) -> None:
        cfg_step = PipelineConfig(
            run=RunConfig(command=_TEST_COMMAND, run_only="download-data"))
        names_step = self._names_from_builder(cfg_step)
        self.assertEqual(names_step, ["download-data"])

        with self.assertRaisesRegex(ValueError, "run_only step not found"):
            self._names_from_builder(
                PipelineConfig(
                    run=RunConfig(command=_TEST_COMMAND, run_only="nope")))
        with self.assertRaisesRegex(ValueError, "run_only step not found"):
            self._names_from_builder(
                PipelineConfig(run=RunConfig(command=_TEST_COMMAND,
                                             run_only="download.nope")))

    def test_force_semantics(self) -> None:
        cfg_all = PipelineConfig(
            run=RunConfig(command=_TEST_COMMAND, force=True))
        names_all = self._names_from_builder(cfg_all)
        self.assertEqual(names_all, [
            "download-data",
            "download-metadata",
            "create-sample",
            "create-schema-mapping",
            "process-full-data",
            "create-dc-config",
        ])

    def test_timestamp_chaining_triggers_next_step(self) -> None:
        newer = 2_000
        older = 1_000
        state = self._state_with({
            "download-data": (1, "succeeded", newer),
            "download-metadata": (1, "succeeded", older),
            "create-sample": (1, "succeeded", older),
            "create-schema-mapping": (1, "succeeded", older),
            "process-full-data": (1, "succeeded", older),
            "create-dc-config": (1, "succeeded", older),
        })
        cfg = PipelineConfig(run=RunConfig(command=_TEST_COMMAND))
        names = self._names_from_builder(cfg, state=state)
        self.assertEqual(names, [
            "download-metadata",
            "create-sample",
            "create-schema-mapping",
            "process-full-data",
            "create-dc-config",
        ])

    def test_force_branch_records_decisions(self) -> None:
        cfg = PipelineConfig(run=RunConfig(command=_TEST_COMMAND, force=True))
        steps = build_steps(cfg)
        builder = PipelineBuilder(config=cfg,
                                  state=self._empty_state(),
                                  steps=steps)
        result = builder.build()
        self.assertEqual(len(result.decisions), len(steps))
        for decision in result.decisions:
            self.assertEqual(decision.decision, StepDecision.RUN)
            self.assertIn("Force flag set", decision.reason)

    def test_run_only_ignores_timestamp_chaining(self) -> None:
        newer = 4_000
        older = 3_000
        state = self._state_with({
            "download-data": (1, "succeeded", newer),
            "download-metadata": (1, "succeeded", older),
        })
        cfg = PipelineConfig(
            run=RunConfig(command=_TEST_COMMAND, run_only="download-data"))
        names = self._names_from_builder(cfg, state=state)
        self.assertEqual(names, ["download-data"])

    def test_version_bump_schedules_downstream(self) -> None:
        steps = [
            _VersionedStep("download-data", 1),
            _VersionedStep("process-full-data", 2),
            _VersionedStep("create-dc-config", 1),
        ]
        state = self._state_with({
            "download-data": (1, "succeeded", 1000),
            "process-full-data": (1, "succeeded", 1000),
            "create-dc-config": (1, "succeeded", 1000),
        })
        cfg = PipelineConfig(run=RunConfig(command=_TEST_COMMAND))
        names = self._names_from_builder(cfg, steps, state)
        self.assertEqual(names, ["process-full-data", "create-dc-config"])

        pipeline = build_sdmx_pipeline(config=cfg, state=state, steps=steps)
        self.assertEqual([s.name for s in pipeline.get_steps()],
                         ["process-full-data", "create-dc-config"])

    def test_incremental_records_skip_reasons(self) -> None:
        state = self._state_with({
            "download-data": (1, "succeeded", 1_000),
            "download-metadata": (1, "succeeded", 1_000),
            "create-sample": (1, "succeeded", 1_000),
            "create-schema-mapping": (1, "succeeded", 1_000),
            "process-full-data": (1, "succeeded", 1_000),
            "create-dc-config": (1, "succeeded", 1_000),
        })
        cfg = PipelineConfig(run=RunConfig(command=_TEST_COMMAND))
        steps = build_steps(cfg)
        builder = PipelineBuilder(config=cfg, state=state, steps=steps)
        result = builder.build()
        self.assertFalse(result.pipeline.get_steps())
        self.assertEqual(len(result.decisions), len(steps))
        for decision in result.decisions:
            self.assertEqual(decision.decision, StepDecision.SKIP)
            self.assertIn("up-to-date", decision.reason)


class SdmxTestBase(unittest.TestCase):

    def setUp(self) -> None:
        self._tmpdir_obj = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir_obj.cleanup)
        self._tmpdir = self._tmpdir_obj.name

    def _create_test_input_files(self, prefix: str) -> None:
        (Path(self._tmpdir) / f"{prefix}_data.csv").write_text("data")
        (Path(self._tmpdir) / f"{prefix}_sample.csv").write_text("sample")
        (Path(self._tmpdir) / f"{prefix}_metadata.xml").write_text("metadata")

        sample_output_dir = Path(self._tmpdir) / "sample_output"
        sample_output_dir.mkdir(parents=True, exist_ok=True)
        (sample_output_dir / f"{prefix}_pvmap.csv").write_text("pvmap")
        (sample_output_dir / f"{prefix}_metadata.csv").write_text("metadata")

        output_dir = Path(self._tmpdir) / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / f"{prefix}.csv").write_text("output")

    def _build_config(self,
                      dataset_prefix: str | None,
                      dataflow: str | None = "FLOW",
                      command: str = "test",
                      endpoint: str = "https://example.com",
                      agency: str = "AGENCY") -> PipelineConfig:
        return PipelineConfig(
            sdmx=SdmxConfig(
                endpoint=endpoint,
                agency=agency,
                dataflow=SdmxDataflowConfig(
                    id=dataflow,
                    key="test-key",
                    param="area=US",
                ),
            ),
            run=RunConfig(
                dataset_prefix=dataset_prefix,
                working_dir=self._tmpdir,
                skip_confirmation=True,
                command=command,
            ),
        )


class RunPipelineTest(SdmxTestBase):

    def setUp(self) -> None:
        super().setUp()
        # Mock _run_command to avoid actual execution during pipeline tests
        self._run_command_patcher = mock.patch(
            "tools.agentic_import.sdmx_import_pipeline._run_command")
        self._mock_run_command = self._run_command_patcher.start()
        self.addCleanup(self._run_command_patcher.stop)

    def test_run_pipeline_updates_state_and_hash(self) -> None:
        command = "sdmx run pipeline"
        config = self._build_config(dataset_prefix="demo",
                                    dataflow="df.1",
                                    command=command)
        clock = _IncrementingClock(datetime(2025, 1, 1, tzinfo=timezone.utc),
                                   timedelta(seconds=1))

        # Create test files for ProcessFullDataStep
        self._create_test_input_files("demo")

        run_sdmx_pipeline(config=config, now_fn=clock)

        state_path = Path(self._tmpdir) / ".datacommons" / "demo.state.json"
        self.assertTrue(state_path.exists())
        with state_path.open(encoding="utf-8") as fp:
            state = json.load(fp)

        expected_hash = hashlib.sha256(
            json.dumps(
                {
                    "sdmx.agency": config.sdmx.agency,
                    "sdmx.dataflow.id": config.sdmx.dataflow.id,
                    "sdmx.endpoint": config.sdmx.endpoint,
                    "sdmx.dataflow.key": config.sdmx.dataflow.key,
                    "sdmx.dataflow.param": config.sdmx.dataflow.param,
                },
                sort_keys=True,
                separators=(",", ":")).encode("utf-8")).hexdigest()

        self.assertEqual(state["dataset_prefix"], "demo")
        self.assertEqual(state["command"], command)
        self.assertEqual(state["critical_input_hash"], expected_hash)
        self.assertEqual(len(state["steps"]), 6)

        for step_name in [
                "download-data", "download-metadata", "create-sample",
                "create-schema-mapping", "process-full-data", "create-dc-config"
        ]:
            self.assertIn(step_name, state["steps"])
            self.assertEqual(state["steps"][step_name]["status"], "succeeded")

    def test_run_id_sanitizes_dataflow_when_prefix_missing(self) -> None:
        dataflow = "My Flow-Name 2025!!!"
        config = self._build_config(dataset_prefix=None,
                                    dataflow=dataflow,
                                    command="sdmx run sanitized")

        # Create test files for ProcessFullDataStep with sanitized name
        sanitized_prefix = "my_flow_name_2025"
        self._create_test_input_files(sanitized_prefix)

        run_sdmx_pipeline(config=config,
                          now_fn=_IncrementingClock(
                              datetime(2025, 1, 2, tzinfo=timezone.utc),
                              timedelta(seconds=2)))

        expected_run_id = "my_flow_name_2025"
        state_path = Path(
            self._tmpdir) / ".datacommons" / f"{expected_run_id}.state.json"
        self.assertTrue(state_path.exists())
        with state_path.open(encoding="utf-8") as fp:
            state = json.load(fp)
        self.assertEqual(state["dataset_prefix"], expected_run_id)

    def test_invalid_working_dir_raises(self) -> None:
        path = Path(self._tmpdir) / "not_a_dir"
        path.write_text("content")
        base_config = self._build_config(dataset_prefix="demo",
                                         dataflow="df",
                                         command="sdmx run invalid")
        updated_run = dataclasses.replace(base_config.run,
                                          working_dir=str(path))
        config = dataclasses.replace(base_config, run=updated_run)
        with self.assertRaisesRegex(ValueError,
                                    "working_dir is not a directory"):
            run_sdmx_pipeline(config=config)

    def test_hash_change_forces_full_rerun(self) -> None:
        config = self._build_config(dataset_prefix="demo",
                                    dataflow="df.2",
                                    command="sdmx rerun force")
        first_clock = _IncrementingClock(
            datetime(2025, 1, 2, tzinfo=timezone.utc), timedelta(seconds=1))

        # Create test files for ProcessFullDataStep
        self._create_test_input_files("demo")

        # Run 1 with original config
        run_sdmx_pipeline(config=config, now_fn=first_clock)

        state_path = Path(self._tmpdir) / ".datacommons" / "demo.state.json"
        with state_path.open(encoding="utf-8") as fp:
            first_state = json.load(fp)

        updated_dataflow = dataclasses.replace(config.sdmx.dataflow,
                                               key="changed-key")
        updated_sdmx = dataclasses.replace(config.sdmx,
                                           dataflow=updated_dataflow)
        updated_config = dataclasses.replace(config, sdmx=updated_sdmx)
        second_clock = _IncrementingClock(
            datetime(2025, 1, 3, tzinfo=timezone.utc), timedelta(seconds=1))
        run_sdmx_pipeline(config=updated_config, now_fn=second_clock)

        with state_path.open(encoding="utf-8") as fp:
            second_state = json.load(fp)

        self.assertNotEqual(first_state["critical_input_hash"],
                            second_state["critical_input_hash"])
        self.assertGreater(
            second_state["steps"]["download-data"]["ended_at_ts"],
            first_state["steps"]["download-data"]["ended_at_ts"])

    def test_hash_unchanged_skips_rerun(self) -> None:
        config = self._build_config(dataset_prefix="demo",
                                    dataflow="df.3",
                                    command="sdmx rerun noop")
        initial_clock = _IncrementingClock(
            datetime(2025, 1, 3, tzinfo=timezone.utc), timedelta(seconds=1))

        # Create test files for ProcessFullDataStep
        self._create_test_input_files("demo")

        # Run 1
        run_sdmx_pipeline(config=config, now_fn=initial_clock)

        state_path = Path(self._tmpdir) / ".datacommons" / "demo.state.json"
        with state_path.open(encoding="utf-8") as fp:
            first_state = json.load(fp)

        later_clock = _IncrementingClock(
            datetime(2025, 1, 7, tzinfo=timezone.utc), timedelta(seconds=1))
        run_sdmx_pipeline(config=config, now_fn=later_clock)

        with state_path.open(encoding="utf-8") as fp:
            second_state = json.load(fp)

        self.assertEqual(first_state, second_state)


class SdmxStepTest(SdmxTestBase):

    def _assert_run_and_dry_run_use_same_plan(self,
                                              step,
                                              *,
                                              log_contains: str,
                                              cmd_contains: str,
                                              extra_cmd_checks=None,
                                              expect_verbose: bool = True
                                              ) -> None:
        extra_cmd_checks = extra_cmd_checks or []
        with mock.patch("tools.agentic_import.sdmx_import_pipeline._run_command"
                       ) as mock_run_cmd:
            with self.assertLogs(logging.get_absl_logger(),
                                 level="INFO") as logs:
                step.dry_run()
                step.run()

        self.assertTrue(
            any("test-step (dry run): would run" in entry
                for entry in logs.output))
        self.assertTrue(any(log_contains in entry for entry in logs.output))
        mock_run_cmd.assert_called_once()
        args, kwargs = mock_run_cmd.call_args
        command = args[0]
        self.assertTrue(any(cmd_contains in arg for arg in command))
        self.assertEqual(kwargs["verbose"], expect_verbose)
        for check in extra_cmd_checks:
            check(command)

    def _assert_step_caches_plan(self,
                                 step,
                                 *,
                                 command_contains=None,
                                 path_attrs=None) -> None:
        command_contains = command_contains or []
        path_attrs = path_attrs or []

        context1 = step._prepare_command()
        context2 = step._prepare_command()
        self.assertIs(context1, context2)

        for attr in path_attrs:
            self.assertTrue(getattr(context1, attr).is_absolute())

        if command_contains:
            for expected in command_contains:
                self.assertTrue(
                    any(expected in arg for arg in context1.full_command))

    def test_run_command_logs_and_executes(self) -> None:
        with mock.patch("subprocess.run") as mock_run:
            with self.assertLogs(logging.get_absl_logger(),
                                 level="DEBUG") as logs:
                _run_command(["echo", "hello"], verbose=True)

            mock_run.assert_called_once_with(["echo", "hello"], check=True)
            self.assertTrue(
                any("Running command: echo hello" in entry
                    for entry in logs.output))

    def test_download_metadata_step_caches_plan(self) -> None:
        config = PipelineConfig(
            sdmx=SdmxConfig(
                endpoint="https://example.com",
                agency="AGENCY",
                dataflow=SdmxDataflowConfig(id="FLOW"),
            ),
            run=RunConfig(
                command="test",
                dataset_prefix="demo",
                working_dir=self._tmpdir,
                verbose=True,
            ),
        )
        step = DownloadMetadataStep(name="test-step", config=config)
        self._assert_step_caches_plan(
            step,
            command_contains=["download-metadata", "--endpoint=https://example.com"],
            path_attrs=["output_path"],
        )

    def test_download_metadata_step_run_and_dry_run_use_same_plan(self) -> None:
        config = PipelineConfig(
            sdmx=SdmxConfig(
                endpoint="https://example.com",
                agency="AGENCY",
                dataflow=SdmxDataflowConfig(id="FLOW"),
            ),
            run=RunConfig(
                command="test",
                dataset_prefix="demo",
                working_dir=self._tmpdir,
                verbose=True,
            ),
        )
        step = DownloadMetadataStep(name="test-step", config=config)
        self._assert_run_and_dry_run_use_same_plan(
            step,
            log_contains="download-metadata",
            cmd_contains="download-metadata",
        )

    def test_download_data_step_caches_plan(self) -> None:
        config = PipelineConfig(
            sdmx=SdmxConfig(
                endpoint="https://example.com",
                agency="AGENCY",
                dataflow=SdmxDataflowConfig(
                    id="FLOW",
                    key="test-key",
                    param="area=US",
                ),
            ),
            run=RunConfig(
                command="test",
                dataset_prefix="demo",
                working_dir=self._tmpdir,
                verbose=True,
            ),
        )
        step = DownloadDataStep(name="test-step", config=config)
        self._assert_step_caches_plan(
            step,
            command_contains=[
                "download-data",
                "--endpoint=https://example.com",
                "--key=test-key",
                "--param=area=US",
            ],
            path_attrs=["output_path"],
        )

    def test_download_data_step_run_and_dry_run_use_same_plan(self) -> None:
        config = PipelineConfig(
            sdmx=SdmxConfig(
                endpoint="https://example.com",
                agency="AGENCY",
                dataflow=SdmxDataflowConfig(id="FLOW"),
            ),
            run=RunConfig(
                command="test",
                dataset_prefix="demo",
                working_dir=self._tmpdir,
                verbose=True,
            ),
        )
        step = DownloadDataStep(name="test-step", config=config)
        self._assert_run_and_dry_run_use_same_plan(
            step,
            log_contains="download-data",
            cmd_contains="download-data",
        )

    def test_create_sample_step_caches_plan(self) -> None:
        config = PipelineConfig(
            run=RunConfig(
                command="test",
                dataset_prefix="demo",
                working_dir=self._tmpdir,
                verbose=True,
            ),
            sample=SampleConfig(rows=500),
        )
        step = CreateSampleStep(name="test-step", config=config)
        self._assert_step_caches_plan(
            step,
            command_contains=["data_sampler.py", "--sampler_output_rows=500"],
            path_attrs=["output_path"],
        )

    def test_create_sample_step_run_and_dry_run_use_same_plan(self) -> None:
        config = PipelineConfig(
            run=RunConfig(
                command="test",
                dataset_prefix="demo",
                working_dir=self._tmpdir,
                verbose=True,
            ),
            sample=SampleConfig(rows=500),
        )
        step = CreateSampleStep(name="test-step", config=config)

        # Create test input file for run()
        input_path = Path(self._tmpdir) / "demo_data.csv"
        input_path.write_text("header\nrow1")
        self._assert_run_and_dry_run_use_same_plan(
            step,
            log_contains="data_sampler.py",
            cmd_contains="data_sampler.py",
        )

    def test_create_sample_step_dry_run_succeeds_if_input_missing(self) -> None:
        config = PipelineConfig(
            run=RunConfig(
                command="test",
                dataset_prefix="demo",
                working_dir=self._tmpdir,
                verbose=True,
            ),
            sample=SampleConfig(rows=500),
        )
        step = CreateSampleStep(name="test-step", config=config)
        # No input file created, dry run should still succeed
        step.dry_run()

    def test_create_sample_step_run_fails_if_input_missing(self) -> None:
        config = PipelineConfig(
            run=RunConfig(
                command="test",
                dataset_prefix="demo",
                working_dir=self._tmpdir,
                verbose=True,
            ),
            sample=SampleConfig(rows=500),
        )
        step = CreateSampleStep(name="test-step", config=config)
        # No input file created, run should fail
        with self.assertRaisesRegex(RuntimeError,
                                    "Input file missing for sampling"):
            step.run()

    def test_create_schema_map_step_caches_plan(self) -> None:
        config = PipelineConfig(run=RunConfig(
            command="test",
            dataset_prefix="demo",
            working_dir=self._tmpdir,
            verbose=True,
            gemini_cli="custom-gemini",
            skip_confirmation=True,
        ),)
        step = CreateSchemaMapStep(name="test-step", config=config)
        self._assert_step_caches_plan(
            step,
            command_contains=[
                "pvmap_generator.py",
                "--gemini_cli=custom-gemini",
                "--skip_confirmation",
            ],
            path_attrs=["sample_path", "metadata_path", "output_prefix"],
        )

    def test_create_schema_map_step_run_and_dry_run_use_same_plan(self) -> None:
        config = PipelineConfig(run=RunConfig(
            command="test",
            dataset_prefix="demo",
            working_dir=self._tmpdir,
            verbose=True,
        ),)
        step = CreateSchemaMapStep(name="test-step", config=config)

        # Create test input files for run()
        (Path(self._tmpdir) / "demo_sample.csv").write_text("header\nrow1")
        (Path(self._tmpdir) / "demo_metadata.xml").write_text("<xml/>")
        self._assert_run_and_dry_run_use_same_plan(
            step,
            log_contains="pvmap_generator.py",
            cmd_contains="pvmap_generator.py",
        )

    def test_create_schema_map_step_dry_run_succeeds_if_input_missing(
            self) -> None:
        config = PipelineConfig(run=RunConfig(
            command="test",
            dataset_prefix="demo",
            working_dir=self._tmpdir,
            verbose=True,
        ),)
        step = CreateSchemaMapStep(name="test-step", config=config)
        # No input files created, dry run should still succeed
        step.dry_run()

    def test_create_schema_map_step_run_fails_if_input_missing(self) -> None:
        config = PipelineConfig(run=RunConfig(
            command="test",
            dataset_prefix="demo",
            working_dir=self._tmpdir,
            verbose=True,
        ),)
        step = CreateSchemaMapStep(name="test-step", config=config)
        # No input files created, run should fail
        with self.assertRaises(RuntimeError):
            step.run()

    def test_process_full_data_step_caches_plan(self) -> None:
        config = PipelineConfig(run=RunConfig(
            command="test",
            dataset_prefix="demo",
            working_dir=self._tmpdir,
            verbose=True,
        ),)
        step = ProcessFullDataStep(name="test-step", config=config)
        self._assert_step_caches_plan(
            step,
            path_attrs=[
                "input_data_path",
                "pv_map_path",
                "metadata_path",
                "output_prefix",
            ],
        )

    def test_process_full_data_step_run_and_dry_run_use_same_plan(self) -> None:
        config = PipelineConfig(run=RunConfig(
            command="test",
            dataset_prefix="demo",
            working_dir=self._tmpdir,
            verbose=True,
        ),)
        step = ProcessFullDataStep(name="test-step", config=config)

        # Create test files
        self._create_test_input_files("demo")
        self._assert_run_and_dry_run_use_same_plan(
            step,
            log_contains="stat_var_processor.py",
            cmd_contains="stat_var_processor.py",
            extra_cmd_checks=[
                lambda command: self.assertTrue(
                    any(arg.startswith("--input_data=") for arg in command)),
            ],
        )

    def test_process_full_data_step_dry_run_succeeds_if_input_missing(
            self) -> None:
        config = PipelineConfig(run=RunConfig(
            command="test",
            dataset_prefix="demo",
            working_dir=self._tmpdir,
            verbose=True,
        ),)
        step = ProcessFullDataStep(name="test-step", config=config)
        # Missing input files, dry run should still succeed
        step.dry_run()

    def test_process_full_data_step_run_fails_if_input_missing(self) -> None:
        config = PipelineConfig(run=RunConfig(
            command="test",
            dataset_prefix="demo",
            working_dir=self._tmpdir,
            verbose=True,
        ),)
        step = ProcessFullDataStep(name="test-step", config=config)
        # Missing input files, run should fail
        with self.assertRaises(RuntimeError):
            step.run()

    def test_create_dc_config_step_caches_plan(self) -> None:
        config = self._build_config(dataset_prefix="demo",
                                    endpoint="https://example.com",
                                    agency="AGENCY",
                                    dataflow="FLOW")
        step = CreateDcConfigStep(name="test-step", config=config)
        self._assert_step_caches_plan(
            step,
            path_attrs=["input_csv", "output_config"],
        )

    def test_create_dc_config_step_run_and_dry_run_use_same_plan(self) -> None:
        config = self._build_config(dataset_prefix="demo",
                                    endpoint="https://example.com",
                                    agency="AGENCY",
                                    dataflow="FLOW")
        step = CreateDcConfigStep(name="test-step", config=config)

        # Create test files
        self._create_test_input_files("demo")
        # Create final output dir and input csv
        final_output_dir = Path(self._tmpdir) / "output"
        final_output_dir.mkdir(parents=True, exist_ok=True)
        (final_output_dir / "demo.csv").write_text("data")
        self._assert_run_and_dry_run_use_same_plan(
            step,
            log_contains="generate_custom_dc_config.py",
            cmd_contains="generate_custom_dc_config.py",
            extra_cmd_checks=[
                lambda command: self.assertIn(
                    f"--input_csv={final_output_dir}/demo.csv", command),
                lambda command: self.assertIn(
                    f"--output_config={final_output_dir}/demo_config.json",
                    command),
                lambda command: self.assertIn("--provenance_name=FLOW",
                                              command),
                lambda command: self.assertIn("--source_name=AGENCY", command),
                lambda command: self.assertIn(
                    "--data_source_url=https://example.com", command),
                lambda command: self.assertIn(
                    "--dataset_url=https://example.com/data/AGENCY,FLOW,",
                    command),
            ],
            expect_verbose=False,
        )


if __name__ == "__main__":
    unittest.main()
