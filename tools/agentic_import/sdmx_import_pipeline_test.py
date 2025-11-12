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

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
_PROJECT_ROOT = os.path.dirname(_REPO_ROOT)
for path in (_PROJECT_ROOT,):
    if path not in sys.path:
        sys.path.append(path)

from tools.agentic_import.pipeline import (  # pylint: disable=import-error
    BaseStep, CompositeCallback, Pipeline, PipelineAbort, PipelineRunner,
    RunnerConfig,
)
from tools.agentic_import.sdmx_import_pipeline import (  # pylint: disable=import-error
    CreateDcConfigStep, DownloadDataStep, ProcessFullDataStep,
    InteractiveCallback, JSONStateCallback, PipelineBuilder, PipelineConfig,
    PhaseRegistry, PhaseSpec, StepSpec, SdmxStep, build_pipeline_callback,
    build_registry, build_sdmx_pipeline)
from tools.agentic_import.state_handler import (  # pylint: disable=import-error
    PipelineState, StateHandler, StepState)


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


class _RecordingStep(BaseStep):

    def __init__(self, name: str, *, should_fail: bool = False) -> None:
        super().__init__(name=name, version=1)
        self._should_fail = should_fail

    def run(self) -> None:
        if self._should_fail:
            raise ValueError("boom")

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
            run_id="demo",
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
        self.assertEqual(state["run_id"], "demo")
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
                "run_id": "previous",
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

            class _AbortStep(BaseStep):

                def __init__(self) -> None:
                    super().__init__(name="download.download-data", version=1)

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
                run_id="demo",
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
                    run_id="demo",
                    critical_input_hash="abc",
                    command="python run",
                    skip_confirmation=False,
                )
        self.assertIsInstance(callback, CompositeCallback)


class PlanningTest(unittest.TestCase):

    def _mk_registry(self) -> PhaseRegistry:
        return build_registry()

    def _empty_state(self) -> PipelineState:
        return PipelineState(run_id="demo",
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
        return PipelineState(run_id="demo",
                             critical_input_hash="",
                             command="",
                             updated_at="",
                             updated_at_ts=None,
                             steps=steps)

    def _names_from_builder(self,
                            cfg: PipelineConfig,
                            reg: PhaseRegistry,
                            state: PipelineState | None = None) -> list[str]:
        builder = PipelineBuilder(config=cfg,
                                  state=state or self._empty_state(),
                                  registry=reg)
        pipeline = builder.build()
        return [step.name for step in pipeline.get_steps()]

    def test_run_only_phase_and_step(self) -> None:
        reg = self._mk_registry()
        cfg_phase = PipelineConfig(run_only="download")
        names_phase = self._names_from_builder(cfg_phase, reg)
        self.assertEqual(
            names_phase,
            ["download.download-data", "download.download-metadata"])

        cfg_step = PipelineConfig(run_only="download.download-data")
        names_step = self._names_from_builder(cfg_step, reg)
        self.assertEqual(names_step, ["download.download-data"])

        with self.assertRaisesRegex(ValueError, "run_only phase not found"):
            self._names_from_builder(PipelineConfig(run_only="nope"), reg)
        with self.assertRaisesRegex(ValueError, "run_only step not found"):
            self._names_from_builder(PipelineConfig(run_only="download.nope"),
                                     reg)

    def test_force_semantics(self) -> None:
        reg = self._mk_registry()
        cfg_all = PipelineConfig(force=True)
        names_all = self._names_from_builder(cfg_all, reg)
        self.assertEqual(names_all, [
            "download.download-data",
            "download.download-metadata",
            "sample.create-sample",
            "schema_map.create-schema-mapping",
            "transform.process-full-data",
            "transform.create-dc-config",
        ])

        cfg_phase = PipelineConfig(run_only="download", force=True)
        names_phase = self._names_from_builder(cfg_phase, reg)
        self.assertEqual(
            names_phase,
            ["download.download-data", "download.download-metadata"])

    def test_timestamp_chaining_triggers_next_step(self) -> None:
        reg = self._mk_registry()
        newer = 2_000
        older = 1_000
        state = self._state_with({
            "download.download-data": (1, "succeeded", newer),
            "download.download-metadata": (1, "succeeded", older),
            "sample.create-sample": (1, "succeeded", older),
            "schema_map.create-schema-mapping": (1, "succeeded", older),
            "transform.process-full-data": (1, "succeeded", older),
            "transform.create-dc-config": (1, "succeeded", older),
        })
        cfg = PipelineConfig()
        names = self._names_from_builder(cfg, reg, state)
        self.assertEqual(names, [
            "download.download-metadata",
            "sample.create-sample",
            "schema_map.create-schema-mapping",
            "transform.process-full-data",
            "transform.create-dc-config",
        ])

    def test_run_only_ignores_timestamp_chaining(self) -> None:
        reg = self._mk_registry()
        newer = 4_000
        older = 3_000
        state = self._state_with({
            "download.download-data": (1, "succeeded", newer),
            "download.download-metadata": (1, "succeeded", older),
        })
        cfg = PipelineConfig(run_only="download")
        names = self._names_from_builder(cfg, reg, state)
        self.assertEqual(
            names, ["download.download-data", "download.download-metadata"])

    def test_version_bump_schedules_downstream(self) -> None:
        reg = PhaseRegistry(phases=[
            PhaseSpec(name="download",
                      steps=[
                          StepSpec(
                              phase="download",
                              name="download-data",
                              version=1,
                              factory=lambda cfg: DownloadDataStep(
                                  name="download.download-data", config=cfg)),
                      ]),
            PhaseSpec(name="transform",
                      steps=[
                          StepSpec(phase="transform",
                                   name="process-full-data",
                                   version=2,
                                   factory=lambda cfg: ProcessFullDataStep(
                                       name="transform.process-full-data",
                                       config=cfg)),
                          StepSpec(phase="transform",
                                   name="create-dc-config",
                                   version=1,
                                   factory=lambda cfg: CreateDcConfigStep(
                                       name="transform.create-dc-config",
                                       config=cfg)),
                      ])
        ])
        state = self._state_with({
            "download.download-data": (1, "succeeded", 1000),
            "transform.process-full-data": (1, "succeeded", 1000),
            "transform.create-dc-config": (1, "succeeded", 1000),
        })
        cfg = PipelineConfig()
        names = self._names_from_builder(cfg, reg, state)
        self.assertEqual(
            names,
            ["transform.process-full-data", "transform.create-dc-config"])

        pipeline = build_sdmx_pipeline(config=cfg, state=state, registry=reg)
        self.assertEqual(
            [s.name for s in pipeline.get_steps()],
            ["transform.process-full-data", "transform.create-dc-config"])


if __name__ == "__main__":
    unittest.main()
