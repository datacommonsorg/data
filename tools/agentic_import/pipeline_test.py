#!/usr/bin/env python3
"""Unit tests for the Phase 0 pipeline skeleton."""

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


if __name__ == "__main__":
    unittest.main()
