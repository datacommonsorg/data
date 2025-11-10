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

"""Unit tests for the Phase 1 JSON state callback."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
_PROJECT_ROOT = os.path.dirname(_REPO_ROOT)
for path in (_PROJECT_ROOT,):
    if path not in sys.path:
        sys.path.append(path)

from tools.agentic_import.pipeline import (  # pylint: disable=import-error
    BaseStep,
    Pipeline,
    PipelineRunner,
    RunnerConfig,
)
from tools.agentic_import.sdmx_import_pipeline import (  # pylint: disable=import-error
    JSONStateCallback,
)


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

    def dry_run(self) -> str:
        return "noop"


class JSONStateCallbackTest(unittest.TestCase):

    def _build_callback(self, *, tmpdir: str,
                        clock: _IncrementingClock) -> JSONStateCallback:
        state_path = os.path.join(tmpdir, ".datacommons", "demo.state.json")
        return JSONStateCallback(
            state_path=state_path,
            run_id="demo",
            critical_input_hash="abc123",
            command="python run",
            now_fn=clock,
        )

    def test_successful_step_persists_expected_schema(self) -> None:
        clock = _IncrementingClock(
            datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc),
            timedelta(seconds=5))
        with tempfile.TemporaryDirectory() as tmpdir:
            callback = self._build_callback(tmpdir=tmpdir, clock=clock)
            pipeline = Pipeline(steps=[_RecordingStep("download.download-data")])
            runner = PipelineRunner(RunnerConfig())
            runner.run(pipeline, callback)

            state_path = os.path.join(tmpdir, ".datacommons", "demo.state.json")
            with open(state_path, encoding="utf-8") as fp:
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

    def test_failed_step_records_error_and_persists_file(self) -> None:
        clock = _IncrementingClock(
            datetime(2025, 1, 2, 0, 0, tzinfo=timezone.utc),
            timedelta(seconds=7))
        with tempfile.TemporaryDirectory() as tmpdir:
            callback = self._build_callback(tmpdir=tmpdir, clock=clock)
            pipeline = Pipeline(
                steps=[_RecordingStep("sample.create-sample", should_fail=True)])
            runner = PipelineRunner(RunnerConfig())

            with self.assertRaisesRegex(ValueError, "boom"):
                runner.run(pipeline, callback)

            state_path = os.path.join(tmpdir, ".datacommons", "demo.state.json")
            with open(state_path, encoding="utf-8") as fp:
                state = json.load(fp)

        step_state = state["steps"]["sample.create-sample"]
        self.assertEqual(step_state["status"], "failed")
        self.assertIn("boom", step_state["message"])
        self.assertAlmostEqual(step_state["duration_s"], 7.0)


if __name__ == "__main__":
    unittest.main()
