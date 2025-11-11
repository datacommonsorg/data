# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Generic building blocks for lightweight agentic pipelines.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Sequence

from absl import logging


class PipelineAbort(Exception):
    """Raised when pipeline execution should stop early for any reason."""


class Step(abc.ABC):
    """Abstract pipeline step interface."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human friendly identifier used for logging."""

    @property
    @abc.abstractmethod
    def version(self) -> int:
        """Version used for invalidation decisions."""

    @abc.abstractmethod
    def run(self) -> None:
        """Execute the step."""

    @abc.abstractmethod
    def dry_run(self) -> None:
        """Log a read-only preview of the work to be done."""


class BaseStep(Step, abc.ABC):
    """Helper base class that stores mandatory metadata."""

    def __init__(self, *, name: str, version: int) -> None:
        if not name:
            raise ValueError("step requires a name")
        self._name = name
        self._version = version

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> int:
        return self._version


@dataclass(frozen=True)
class Pipeline:
    steps: Sequence[Step]

    def get_steps(self) -> list[Step]:
        return list(self.steps)


class PipelineCallback:
    """Lifecycle hooks consumed by the runner; defaults are no-ops."""

    def before_step(self, step: Step) -> None:
        """Called immediately before `step.run()`; raising an error skips execution."""
        del step

    def after_step(self, step: Step, *, error: Exception | None = None) -> None:
        """Runs once per step after `step.run()` succeeds or raises."""
        del step, error


class CompositeCallback(PipelineCallback):
    """Fans out events to child callbacks in order."""

    def __init__(self, callbacks: Sequence[PipelineCallback]) -> None:
        self._callbacks = list(callbacks)

    def before_step(self, step: Step) -> None:
        for callback in self._callbacks:
            callback.before_step(step)

    def after_step(self, step: Step, *, error: Exception | None = None) -> None:
        for callback in self._callbacks:
            callback.after_step(step, error=error)


@dataclass(frozen=True)
class RunnerConfig:
    """Placeholder for future runner toggles."""


class PipelineRunner:

    def __init__(self, config: RunnerConfig | None = None) -> None:
        self._config = config or RunnerConfig()

    def run(self,
            pipeline: Pipeline,
            callback: PipelineCallback | None = None) -> None:
        current_step: Step | None = None
        steps = pipeline.get_steps()
        logging.info(f"Starting pipeline with {len(steps)} steps")
        try:
            for step in steps:
                current_step = step
                logging.info(f"Preparing step {step.name} (v{step.version})")
                if callback:
                    callback.before_step(step)
                error: Exception | None = None
                try:
                    step.run()
                except Exception as exc:  # pylint: disable=broad-except
                    error = exc
                    logging.exception(f"Step {step.name} failed")
                    raise
                finally:
                    if callback:
                        callback.after_step(step, error=error)
                logging.info(f"Finished step {step.name}")
            logging.info("Pipeline completed")
        except PipelineAbort:
            name = current_step.name if current_step else "<none>"
            logging.info(f"Pipeline aborted at {name}")
