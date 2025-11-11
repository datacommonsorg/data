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
"""Unit tests for the agentic pipeline skeleton."""

import os
import sys
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

from pipeline import (  # pylint: disable=import-error
    BaseStep, Pipeline, PipelineAbort, PipelineCallback, PipelineRunner,
    RunnerConfig, Step,
)


class _TrackingStep(BaseStep):

    def __init__(self, name: str, events: list[str]) -> None:
        super().__init__(name=name, version=1)
        self._events = events
        self.executed = False

    def run(self) -> None:
        self.executed = True
        self._events.append(f"run:{self.name}")

    def dry_run(self) -> str:
        return ""


class _FailingStep(BaseStep):

    def __init__(self, *, name: str, version: int) -> None:
        super().__init__(name=name, version=version)

    def run(self) -> None:
        raise ValueError("boom")

    def dry_run(self) -> str:
        return ""


class PipelineRunnerTest(unittest.TestCase):

    def _build_pipeline(self, events: list[str]) -> Pipeline:
        step_one = _TrackingStep("one", events)
        step_two = _TrackingStep("two", events)
        return Pipeline(steps=[step_one, step_two])

    def test_on_before_step_runs_before_each_step(self) -> None:
        events: list[str] = []

        class RecordingCallback(PipelineCallback):

            def before_step(self, step: Step) -> None:
                events.append(f"before:{step.name}")

        pipeline = self._build_pipeline(events)
        PipelineRunner(RunnerConfig()).run(pipeline, RecordingCallback())

        self.assertEqual(
            events,
            [
                "before:one",
                "run:one",
                "before:two",
                "run:two",
            ],
        )

    def test_pipeline_abort_skips_downstream_steps(self) -> None:
        events: list[str] = []
        pipeline = self._build_pipeline(events)
        runner = PipelineRunner(RunnerConfig())

        class AbortOnSecond(PipelineCallback):

            def before_step(self, step: Step) -> None:
                if step.name == "two":
                    raise PipelineAbort("stop")

        runner.run(pipeline, AbortOnSecond())

        self.assertEqual(events, ["run:one"])
        # PipelineAbort is swallowed by the runner, so execution simply stops.

    def test_before_step_exception_skips_after_step(self) -> None:
        events: list[str] = []
        pipeline = Pipeline(steps=[_TrackingStep("one", events)])
        runner = PipelineRunner(RunnerConfig())

        class RecordingCallback(PipelineCallback):

            def before_step(self, step: Step) -> None:
                events.append(f"before:{step.name}")
                raise RuntimeError("boom")

            def after_step(self,
                           step: Step,
                           *,
                           error: Exception | None = None) -> None:
                del step, error
                events.append("after-called")

        with self.assertRaises(RuntimeError):
            runner.run(pipeline, RecordingCallback())

        self.assertEqual(events, ["before:one"])

    def test_after_step_receives_error_when_step_fails(self) -> None:

        class RecordingCallback(PipelineCallback):

            def __init__(self) -> None:
                self.after_calls: list[tuple[str, str | None]] = []

            def after_step(self,
                           step: Step,
                           *,
                           error: Exception | None = None) -> None:
                name = step.name
                error_name = type(error).__name__ if error else None
                self.after_calls.append((name, error_name))

        callback = RecordingCallback()
        pipeline = Pipeline(steps=[_FailingStep(name="fail-step", version=1)])

        with self.assertRaises(ValueError):
            PipelineRunner(RunnerConfig()).run(pipeline, callback)

        self.assertEqual(callback.after_calls, [("fail-step", "ValueError")])


if __name__ == "__main__":
    unittest.main()
