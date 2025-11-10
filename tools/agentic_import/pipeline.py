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
    def dry_run(self) -> str:
        """Return a read-only preview of the work to be done."""


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
        del step

    def after_step(self, step: Step, *, error: Exception | None = None) -> None:
        del step, error


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
        logging.info("Starting pipeline with %d steps", len(steps))
        try:
            for step in steps:
                current_step = step
                logging.info("Preparing step %s (v%d)", step.name, step.version)
                if callback:
                    callback.before_step(step)
                try:
                    step.run()
                except PipelineAbort as exc:
                    if callback:
                        callback.after_step(step, error=exc)
                    raise
                except Exception as exc:  # pylint: disable=broad-except
                    if callback:
                        callback.after_step(step, error=exc)
                    logging.exception("Step %s failed", step.name)
                    raise
                if callback:
                    callback.after_step(step)
                logging.info("Finished step %s", step.name)
            logging.info("Pipeline completed")
        except PipelineAbort as exc:
            name = current_step.name if current_step else "<none>"
            logging.info("Pipeline aborted at %s", name)
